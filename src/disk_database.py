import logging
from config import VERBOSE
import os
import pandas as pd
import csv
import utils
from typing import Optional, Dict, Any


class DiskDatabase():
    def __init__(self, patient_file_name: str, result_file_name: str, history_file_name: str, unpaged_results_file_name: str) -> None:
        """
        Parameters:
        - patient_file_name (str): The filename for storing patient information.
        - result_file_name (str): The filename for storing result information.
        - history_file_name (str): The filename for the history file.
        """
        self.patient_file_name = patient_file_name
        self.result_file_name = result_file_name
        self.unpaged_results_file_name = unpaged_results_file_name

        dtypes_patients = {'MRN': 'int', 'AGE': 'int', 'SEX': 'int'}
        dtypes_results = {'MRN': 'int', 'DATE': 'string', 'RESULT': 'int'}
        dtypes_unpaged_results = {'MRN': 'int', 'DATE': 'string', 'RESULT': 'int'}

        try:
            # Check if the file is empty
            is_empty_patient = os.path.getsize(self.patient_file_name) == 0
        except FileNotFoundError: 
            is_empty_patient = True
        
        try:
            # Check if the file is empty
            is_empty_result = os.path.getsize(self.result_file_name) == 0
        except FileNotFoundError: 
            is_empty_result = True

        try:
            # Check if the file is empty
            is_empty_unpaged_result = os.path.getsize(self.unpaged_results_file_name) == 0
        except FileNotFoundError: 
            is_empty_unpaged_result = True

        # only change the patients, if there is not currently one stored on disk
        if is_empty_patient:
            logging.info("Creating Patients File")
            self.patients_file = pd.DataFrame(columns=['MRN', 'AGE', 'SEX'])
            self.patients_file.to_csv(self.patient_file_name, index=False)
            self.patients_file.astype(dtypes_patients)
        else:
            logging.info(f"Reading Patients File: {self.patient_file_name}")
            self.patients_file = pd.read_csv(self.patient_file_name)
            self.patients_file = self.patients_file.astype(dtypes_patients)
            

        # only use the results file, if there is currently not one stored in disk
        if is_empty_result:
            logging.info(f"Reading History File: {history_file_name}")
            self.results_file = utils.read_file(history_file_name)
            self.results_file = utils.cast_types(self.results_file)
            self.results_file = utils.pivot_rows(self.results_file)
            self.results_file.to_csv(self.result_file_name, index=False)
        else:
            logging.info(f"Reading From Results file: {history_file_name}")
            self.results_file = pd.read_csv(self.result_file_name)
            self.results_file = self.results_file.astype(dtypes_results)
            self.results_file['DATE'] = pd.to_datetime(self.results_file['DATE'])


        if is_empty_unpaged_result:
            logging.info(f"Create unpaged results file")
            self.unpaged_results_file = pd.DataFrame(columns=['MRN', 'DATE', 'RESULT'])
            self.unpaged_results_file.to_csv(self.unpaged_results_file_name, index=False)
            self.unpaged_results_file.astype(dtypes_unpaged_results)
            self.unpaged_results_file['DATE'] = pd.to_datetime(self.unpaged_results_file['DATE'])
        else:
            logging.info(f"Reading Unpaged File: {self.unpaged_results_file_name}")
            self.unpaged_results_file = pd.read_csv(self.unpaged_results_file_name)
            self.unpaged_results_file = self.unpaged_results_file.astype(dtypes_unpaged_results)
            self.unpaged_results_file['DATE'] = pd.to_datetime(self.unpaged_results_file['DATE'])

            

    def admit(self, msg: Dict[str, Any]) -> None:
        """
        Admit a patient based on the provided information.

        Parameters:
        - msg (Dict[str, Any]): Patient information including 'MRN', 'AGE', and 'SEX'.
        """
        if VERBOSE:
            logging.info(f"Admitting patient with MRN: {msg['MRN']}.")
    
        add_to_file = int(msg['MRN']) not in self.patients_file['MRN'].values
        if add_to_file:
            self.patients_file = self.patients_file._append(msg, ignore_index=True)
            with open(self.patient_file_name, 'a') as file:
                writer = csv.writer(file)
                writer.writerow([msg['MRN'], msg['AGE'], msg['SEX']])
        

    def discharge(self, msg: Dict[int, Any]) -> None:
        """
        Discharge a patient based on the provided information.

        Parameters:
        - msg (Dict[int, Any]): Patient information including 'MRN'.
        """
        if VERBOSE:
            mrn = msg['MRN']
            logging.info(f"Discharing patient with MRN: {mrn}.")


    def result(self, msg: Dict[int, Any]) -> None:
        """
        Update the result information for a patient.

        Parameters:
        - msg (Dict[int, Any]): Result information including 'MRN', 'DATE', and 'RESULT'.
        """
        mrn = msg['MRN']
        if VERBOSE:
            logging.info(f"Updating DISK memory:\n  MRN: {mrn}, Result: {msg['RESULT']}.")
        
        self.results_file = self.results_file._append(msg, ignore_index=True)
        with open(self.result_file_name, 'a') as file:
            writer = csv.writer(file)
            writer.writerow([msg['MRN'], msg['DATE'], msg['RESULT']])

    def extract_model_info(self, mrn: int) -> Optional[Dict[int, Any]]:
        """
        Extract model information for a patient.

        Parameters:
        - mrn (int): Medical Record Number.

        Returns:
        - Optional[Dict[int, Any]]: A dictionary containing patient information if patient found, else None
        """
        # get the latest information for the current mrn number
        patient_info = self.patients_file[self.patients_file['MRN'] == mrn]
        patient_result = self.results_file[self.results_file['MRN'] == mrn]

        if len(patient_info) == 0:
            return None

        if len(patient_result) == 0:
            latest_test = None
        else:
            latest_test = patient_result.loc[patient_result['DATE'].idxmax()]
            

        all_info = {
            'AGE': patient_info['AGE'].iloc[0],
            'SEX': patient_info['SEX'].iloc[0],
            'LATEST_DATE': latest_test['DATE'] if latest_test is not None else None,
            'LATEST': latest_test['RESULT'] if latest_test is not None else None
        }

        return all_info
    
    def check_unpaged(self, mrn : int) -> bool:
        """
        When admitting a new patient, checks whether we have an unpaged result for that patient
        Parameters:
        - mrn (int): Medical Record Number.
        """
        unpaged_results = self.unpaged_results_file[self.unpaged_results_file['MRN'] == mrn]
        if len(unpaged_results) == 0:
            return False, None
        
        latest_test = unpaged_results.loc[unpaged_results['DATE'].idxmax()]
        msg = {
            'MRN': mrn,
            'DATE': pd.to_datetime(latest_test['DATE']),
            'RESULT': latest_test['RESULT']
        }
        self.unpaged_results_file = self.unpaged_results_file.drop(
            self.unpaged_results_file[self.unpaged_results_file['MRN'] == mrn].index
        )

        self.unpaged_results_file.to_csv(self.unpaged_results_file_name, index=False)
        return True, msg
    
    def is_admitted(self, mrn: int) -> bool:
        """
        Checks whether the patient is currently in our demographics database
        Parameters:
        - mrn (int): Medical Record Number.
        """
        admit = len(self.patients_file[self.patients_file['MRN'] == mrn]) > 0
        return admit

    def add_unpaged_result(self, msg: Dict[int, Any]) -> None:
        """
        Adds a result to a buffer file, when we do not have that patient in our database
        Parameters:
        - msg (Dict[int, Any]): Result information including 'MRN', 'DATE', and 'RESULT'.
        """
        mrn = msg['MRN']
        if VERBOSE:
            logging.info(f"Updating DISK memory:\n  MRN: {mrn}, Result: {msg['RESULT']}.")
        
        self.unpaged_results_file = self.unpaged_results_file._append(msg, ignore_index=True)
        with open(self.unpaged_results_file_name, 'a') as file:
            writer = csv.writer(file)
            writer.writerow([msg['MRN'], msg['DATE'], msg['RESULT']])

