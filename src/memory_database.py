import logging
from config import VERBOSE, WARNINGS
from disk_database import DiskDatabase
from typing import Optional, Dict, Any


class MemoryDatabase:
    def __init__(self, HDD: DiskDatabase) -> None:
        """
        Initialises the MemoryDatabase.

        Parameters:
        - HDD: The disk database.
        """
        if VERBOSE:
            logging.info("Memory Database initialised.")
        self.data = {}  # In-memory database
        self.HDD = HDD

    def admit(self, msg: Dict[str, Any]) -> None:
        """
        Admits a patient to the in-memory database.

        Parameters:
        - msg (dict): A dictionary containing patient information, including 'MRN', 'AGE', 'SEX'.
        """
        mrn = msg.get('MRN')
        if mrn:
            if VERBOSE:
                logging.info(f"(RAM) Admitting patient with MRN: {mrn}.")
            patient_info = self.HDD.extract_model_info(mrn)
            
            if patient_info is not None:
                self.data[mrn] = patient_info
        else:
            WARNINGS.inc()
            logging.warning("Cannot admit patient without MRN.")

    def result(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates the in-memory database with test result information.

        Parameters:
        - msg (dict): A dictionary containing test result information, including 'MRN', 'RESULT', 'DATE'.

        Returns:
        - dict or None: Updated patient information or None if data is incomplete.
        """
        mrn, result, date = msg.get('MRN'), msg.get('RESULT'), msg.get('DATE')
        if mrn and result and date:
            if VERBOSE:
                logging.info(f"Updating RAM memory:\n  MRN: {mrn}, Result: {result}.")
            
            if mrn in self.data.keys():
                if (self.data[mrn]['LATEST'] or self.data[mrn]['LATEST_DATE']) is None:
                    self.data[mrn]['LATEST_DATE'] = date
                    self.data[mrn]['PRE_LATEST'] = result
                else:
                    self.data[mrn]['PRE_LATEST'] = self.data[mrn]['LATEST']
                
                self.data[mrn]['LATEST'] = result
                self.data[mrn]['TIME_BETWEEN'] = (date - self.data[mrn]['LATEST_DATE']).total_seconds() / 3600
            else:
                logging.info(f"MRN {mrn} not found in RAM.")
                patient_info = self.HDD.extract_model_info(mrn)
                
                if patient_info is not None:
                    self.data[mrn] = patient_info
                    if (self.data[mrn]['LATEST'] or self.data[mrn]['LATEST_DATE']) is None:
                        self.data[mrn]['LATEST_DATE'] = date
                        self.data[mrn]['PRE_LATEST'] = result
                    else:
                        self.data[mrn]['PRE_LATEST'] = self.data[mrn]['LATEST']
                    
                    self.data[mrn]['LATEST'] = result
                    self.data[mrn]['TIME_BETWEEN'] = (date - self.data[mrn]['LATEST_DATE']).total_seconds() / 3600
                else:
                    WARNINGS.inc()
                    logging.warning(f"MRN {mrn} not found in HDD.")
                    return None
        else:
            WARNINGS.inc()
            logging.warning("Incomplete data provided for result update.")
            return None
        return self.data[mrn]

    def discharge(self, msg: Dict[str, Any]) -> None:
        """
        Discharges a patient from the in-memory database.

        Parameters:
        - msg (dict): A dictionary containing the 'MRN' of the patient to be discharged.
        """
        mrn = msg.get('MRN')
        if mrn in self.data.keys():
            if VERBOSE:
                logging.info(f"Removing MRN {mrn} from RAM.")
            self.data.pop(mrn)
        else:
            logging.info(f"MRN {mrn} not found in RAM. Discharged.")
