
from config import VERBOSE, MAX_PAGE_ATTEMPTS, DISCHARGED_PATIENTS, ADMITTED_PATIENTS, RESULTS_COUNTER, HTTP_RECONNECTIONS, FLAG_COUNT, POSITIVE_RATE, MAX_LENGTH_RESULTS, MEDIAN_CREATINE, WARNINGS
from memory_database import MemoryDatabase
from disk_database import DiskDatabase
import logging
from hospital_communication import *
import pandas as pd
import http
from xgboost import XGBClassifier
from typing import Dict, Any
from collections import deque
import numpy as np

results_deque = deque(maxlen=MAX_LENGTH_RESULTS)

class MessageDistributor:
    def __init__(self, loaded_model: XGBClassifier, patient_file_name: str, result_file_name: str, 
                 history_file_name: str, unpaged_results: str) -> None:
        """
        Initialise MessageDistributor.

        Parameters:
        - loaded_model (XGBClassifier): The pre-trained machine learning model.
        """
        self.HDD = DiskDatabase(patient_file_name=patient_file_name, result_file_name=result_file_name, history_file_name=history_file_name, unpaged_results_file_name=unpaged_results)
        self.RAM = MemoryDatabase(self.HDD)
        self.loaded_model = loaded_model

    def admit_patient(self, message: Dict[str, Any]) -> None:
        """
        Process an admission message.

        Parameters:
        - message: Admission message containing patient information.
        """
        ADMITTED_PATIENTS.inc()
        self.HDD.admit(message)
        self.RAM.admit(message)

    def process_result(self, message: Dict[str, Any]) -> str:
        """
        Process a test result message.

        Parameters:
        - message (Dict[str, Any]): Test result message containing patient information and result.
        
        Returns:
        - prediction (str): The model's prediction based on the result.
        """
        RESULTS_COUNTER.inc()
        message = self.RAM.result(message).copy()
        message.pop('LATEST_DATE')
    
        # this might make it slower
        prediction = self.loaded_model.predict(pd.DataFrame(message, index=[1]))[0]
        if VERBOSE:
            logging.info(f'Predicted {prediction}')
        return prediction

    def store_result_history(self, message: Dict[str, Any]) -> None:
        """
        Store the test result in the history on HDD.

        Parameters:
        - message (Dict[str, Any]): Test result message containing patient information and result.
        """
        self.HDD.result(message)

    def discharge_patient(self, message: Dict[str, Any]) -> None:
        """
        Process a discharge message.

        Parameters:
        - message (Dict[str, Any]): Discharge message containing patient information.
        """
        DISCHARGED_PATIENTS.inc()
        self.RAM.discharge(message)
        self.HDD.discharge(message)

    def check_unpaged(self, message: Dict[str, Any]):
        """
        """
        boolean, message = self.HDD.check_unpaged(message['MRN'])
        return boolean, message
    
    def is_admitted(self, mrn: str) -> bool:
        """
        """
        admitted = self.HDD.is_admitted(mrn)
        return admitted
    
    def handle_results_buffer(self, msg) -> None:
        """
        """
        self.HDD.add_unpaged_result(msg)


class MessageProcessor:
    def __init__(self, loaded_model: XGBClassifier, patient_file_name: str, result_file_name: str, history_file_name: str, 
                 unpaged_patients_file_name: str, socket_communication: bool = True) -> None:
        """
        Initialise the MessageProcessor.

        Parameters:
        - loaded_model (XGBClassifier): The pre-trained machine learning model.
        - socket_communication (bool): Boolean that shows whether we are connected to the socket.
        """
        self.distribute = MessageDistributor(loaded_model, patient_file_name, result_file_name, history_file_name, unpaged_patients_file_name)
        self.socket_communication = socket_communication

    def process_message(self, message: str) -> bool:
        """
        Process the received message.

        Parameters:
        - message: The received message.

        Returns:
        - bool: True if the message is a creatinine result, False otherwise.
        """
        unpaged = False
        msg_type = classify_msg(message)
        if msg_type not in ['ADMIT', 'CREATININE', 'DISCHARGE']:
            WARNINGS.inc()
            logging.warning(f'----- PARSING MISTAKE ON FOLLOWING MESSAGE -----\n{message}')

        if msg_type == "ADMIT":
            # first check for unpaged results
            admission_data = parse_admission(admission_msg=message)
            unpaged, creatine_result = self.distribute.check_unpaged(admission_data)
            self.distribute.admit_patient(admission_data)
            if unpaged:
                msg_type = 'CREATININE'
            
        if msg_type == 'CREATININE':
            if unpaged:
                test_data = {
                    'MRN': creatine_result['MRN'],
                    'DATE': pd.to_datetime(creatine_result['DATE']),
                    'RESULT': creatine_result['RESULT']
                }
                date_of_test_unparsed = creatine_result['DATE'].strftime('%Y%m%d%H%M%S')
            else:
                test_data, date_of_test_unparsed = parse_test_result(creatinine_msg=message)
            results_deque.append(test_data['RESULT'])
            MEDIAN_CREATINE.set(np.median(list(results_deque)))
             
            admitted = self.distribute.is_admitted(test_data['MRN'])

            if admitted:
                if self.socket_communication:
                    self.handle_creatinine(test_data, date_of_test_unparsed)
                    return True
            else:
                self.distribute.store_result_history(test_data)
                self.distribute.handle_results_buffer(test_data)
            
        if msg_type == 'DISCHARGE':
            discharge_data = parse_discharge(discharge_msg=message)
            self.distribute.discharge_patient(discharge_data)
            
        return False

    def handle_creatinine(self, test_data: Dict[str, Any], date_of_test_unparsed: str) -> None:
        """
        Handle creatinine result.

        Parameters:
        - test_data (Dict[str, Any]): Parsed creatinine result data.
        - date_of_test_unparsed (str): Date of test (raw)
        """
        self.test_data = test_data
        aki_result = self.distribute.process_result(test_data)
        if aki_result == 1:
            FLAG_COUNT.inc()
            page_attempts = 0
            
            while True and page_attempts < MAX_PAGE_ATTEMPTS:
                
                r = page_aki_alert(str(test_data['MRN']), date_of_test_unparsed)
                page_attempts += 1
                
                if r.status == http.HTTPStatus.OK:
                    HTTP_RECONNECTIONS.inc(int(page_attempts-1))
                    break
            
            if VERBOSE:
                logging.info(f'Paged for patient: {test_data["MRN"]}, {date_of_test_unparsed}')

                if page_attempts == MAX_PAGE_ATTEMPTS:
                    WARNINGS.inc()
                    logging.warning(f'Page attempts exceeded: {test_data["MRN"]}, {date_of_test_unparsed}')
        
        POSITIVE_RATE.set(FLAG_COUNT._value.get() / (RESULTS_COUNTER._value.get()))

    def store_creatine(self) -> None:
        """Store the creatinine result history."""
        self.distribute.store_result_history(self.test_data)
