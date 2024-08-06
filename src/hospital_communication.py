import re
import urllib.request
from config import PAGER_SOCKET, MLLP_START_OF_BLOCK, MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN, MAP_SEX, WARNINGS
from datetime import datetime
import logging
from http.client import HTTPResponse
from typing import List, Dict, Optional, Any

def to_mllp(segments: List[str]) -> bytes:
    """
    Converts a list of HL7 message segments into an MLLP (Minimum Lower Layer Protocol) encoded message.

    Parameters:
    - segments (list): A list of strings, each representing a segment of an HL7 message.

    Returns:
    - bytes: The MLLP encoded message as a byte string. It starts with the MLLP start block character, 
             followed by the HL7 message segments separated by carriage returns, and ends with 
             the MLLP end block and carriage return characters.
    """
    m = bytes(chr(MLLP_START_OF_BLOCK), "ascii")
    m += bytes("\r".join(segments) + "\r", "ascii")
    m += bytes(chr(MLLP_END_OF_BLOCK) + chr(MLLP_CARRIAGE_RETURN), "ascii")
    return m


def from_mllp(buffer: bytes) -> List[str]:
    """
    Decodes an MLLP (Minimum Lower Layer Protocol) encoded message into its HL7 segments.

    Parameters:
    - buffer (bytes): The MLLP encoded message as a byte string.

    Returns:
    - list: A list of strings, where each string is a segment of the original HL7 message.
    """
    return str(buffer[1:-3], "ascii").split("\r") 


def classify_msg(message: List[str]) -> Optional[str]:
    """
    Classifies a given message into one of several predefined categories.

    Parameters:
    - message (list): A list where the first element is expected to contain 
                     the message type identifier.

    Returns:
    - str or None: Returns 'ADMIT' if the message type is 'ADT^A01', 
                   'CREATININE' if the type is 'ORU^R01', 
                   'DISCHARGE' if the type is 'ADT^A03', 
                    or None if the type does not match any of the known types.
    """

    if 'ADT^A01' in message[0]:
        return 'ADMIT'
    
    elif 'ORU^R01' in message[0]:
        return 'CREATININE'
    
    elif 'ADT^A03' in message[0]:
        return 'DISCHARGE'
    
    else:
       WARNINGS.inc()
       logging.warning(f'Unidentified message: {message}')
       return None


def parse_admission(admission_msg: List[str]) -> Dict[str, Any]:
    """
    Parses an admission message to extract relevant information.

    Parameters:
    - admission_msg (list): A list containing the admission message.

    Returns:
    - dict: A dictionary with keys 'MRN', 'DOB', and 'SEX', containing 
            the medical record number, date of birth, and sex of the patient, 
            respectively. Returns None for any field if the information is 
            not found in the message.
    """
    
    reg_pattern = r'(?:[^|]*\|){3}(\d+).*\|(\d{8})\|([MF])'    
    reg_match = re.search(reg_pattern, admission_msg[1])

    if reg_match:
        mrn = reg_match.group(1) if reg_match else None
        date_of_birth = reg_match.group(2) if reg_match else None
        date_of_birth = datetime.strptime(date_of_birth, '%Y%m%d')
        current_date = datetime.today()
        age = current_date.year - date_of_birth.year - ((current_date.month, current_date.day) < (date_of_birth.month, date_of_birth.day))
        sex = reg_match.group(3) if reg_match else None

        extracted = {
            'MRN': int(mrn),
            'AGE': age,
            'SEX': MAP_SEX.get(sex)
            }

        return extracted
    
    else:
        WARNINGS.inc()
        logging.warning(f'Failed to admit patient with message: {admission_msg}')
        return None


def parse_test_result(creatinine_msg: List[str]) -> Dict[str, Any]:
    """
    Parses a test result message to extract relevant information.

    Parameters:
    - creatinine_msg (list): A list containing the creatinine test result message.

    Returns:
    - dict: A dictionary with keys 'MRN', 'DATE', and 'RES', containing 
            the medical record number, date of the test, and test result, 
            respectively. The test result is converted to a float.
    """
    last_numerical_regex = r'(\d+(\.\d+)?)$'
    
    mrn_match = re.search(last_numerical_regex, creatinine_msg[1])
    date_of_test_match = re.search(last_numerical_regex, creatinine_msg[2])
    test_result_match = re.search(last_numerical_regex, creatinine_msg[3])

    if mrn_match and date_of_test_match and test_result_match:

        mrn = mrn_match.group()
        date_of_test_unparsed = date_of_test_match.group()
        test_result = test_result_match.group()

        date_of_test = datetime.strptime(date_of_test_unparsed, '%Y%m%d%H%M%S')

        extracted = {
            'MRN': int(mrn),
            'DATE': date_of_test,
            'RESULT': float(test_result)
        }
        return extracted, date_of_test_unparsed
    
    else:
        WARNINGS.inc()
        logging.warning(f'Failed to parse test result: {creatinine_msg}')
        return None


def parse_discharge(discharge_msg: List[str]) -> Dict[str, Any]:
    """
    Parses a discharge message to extract the medical record number.

    Parameters:
    - discharge_msg (list): A list containing the discharge message.

    Returns:
    - dict: A dictionary with key 'MRN', containing the medical record number.
    """
    last_numerical_regex = r'(\d+(\.\d+)?)$'
    
    mrn_match = re.search(last_numerical_regex, discharge_msg[1])
    
    if mrn_match:
        mrn = mrn_match.group()

        extracted = {
            'MRN':int(mrn)
            }
        
        return extracted
    
    else:
        WARNINGS.inc()
        logging.warning(f'Failed to discharge patient with message: {discharge_msg}')
        return None

def page_aki_alert(mrn: str, date: str) -> HTTPResponse:
    """
    Sends an AKI (Acute Kidney Injury) alert for a given medical record number.

    Parameters:
    - mrn (str): Medical Record Number for the patient.
    - date (str): Date of test (raw)

    Returns:
    - HTTPResponse: The response from the server after the request is made.
    """
    host, num = PAGER_SOCKET.split(':')
    num = int(num)
    data = bytes(','.join([mrn, date]), 'UTF-8') # new API post
    r = urllib.request.urlopen(f"http://{host}:{num}/page", data=data)
    return r