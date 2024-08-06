import acces_main_directory

import unittest
from unittest.mock import Mock, patch
from message_distributor import MessageDistributor, MessageProcessor
from config import PATIENTS_FILE, RESULTS_FILE, HISTORY_FILE, UNPAGED_FILE



class TestMessageDistributor(unittest.TestCase):
    @patch('message_distributor.DiskDatabase')
    @patch('message_distributor.MemoryDatabase')
    def setUp(self, MockMemoryDatabase, MockDiskDatabase):
        self.loaded_model = Mock()
        self.HDD = MockDiskDatabase()
        self.RAM = MockMemoryDatabase(self.HDD)
        self.distributor = MessageDistributor(self.loaded_model, PATIENTS_FILE, RESULTS_FILE, HISTORY_FILE, UNPAGED_FILE,)

    def test_admit_patient(self):
        message = {'patient_id': 1, 'name': 'John Doe'}
        self.distributor.admit_patient(message)
        self.HDD.admit.assert_called_once_with(message)
        self.RAM.admit.assert_called_once_with(message)

    def test_store_result_history(self):
        message = {'patient_id': 1, 'test_result': 4.5}
        self.distributor.store_result_history(message)
        self.HDD.result.assert_called_once_with(message)

    def test_discharge_patient(self):
        message = {'patient_id': 1}
        self.distributor.discharge_patient(message)
        self.RAM.discharge.assert_called_once_with(message)
        self.HDD.discharge.assert_called_once_with(message)


class TestMessageProcessor(unittest.TestCase):
    @patch('message_distributor.MessageDistributor')
    def setUp(self, MockMessageDistributor):
        self.loaded_model = Mock()
        self.input_socket = Mock()
        self.distributor = MockMessageDistributor(self.loaded_model)
        self.processor = MessageProcessor(self.loaded_model, PATIENTS_FILE, RESULTS_FILE, HISTORY_FILE, UNPAGED_FILE, self.input_socket)


    def test_process_message_discharge(self):
        message = 'DISCHARGE|1'
        with patch('message_distributor.classify_msg', return_value='DISCHARGE'), \
                patch('message_distributor.parse_discharge', return_value={'patient_id': 1}):
            self.processor.process_message(message)
            self.distributor.discharge_patient.assert_called_once()

    def test_store_creatine(self):
        self.processor.test_data = {'patient_id': 1, 'test_result': 4.5}
        self.processor.store_creatine()
        self.distributor.store_result_history.assert_called_once()


if __name__ == '__main__':
    unittest.main()
