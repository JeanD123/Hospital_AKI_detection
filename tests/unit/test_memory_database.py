import acces_main_directory

import unittest
from unittest.mock import Mock
from datetime import datetime
from memory_database import MemoryDatabase

class TestMemoryDatabase(unittest.TestCase):
    def setUp(self):
        self.HDD = Mock()
        self.db = MemoryDatabase(self.HDD)

    def test_admit(self):
        msg = {'MRN': '123'}
        self.HDD.extract_model_info.return_value = 'patient_info'
        self.db.admit(msg)
        self.assertEqual(self.db.data['123'], 'patient_info')

    def test_result(self):
        msg = {'MRN': '123', 'RESULT': 100, 'DATE': datetime.strptime('202401202243', '%Y%m%d%H%M')}
        self.db.data['123'] = {'LATEST': None, 'LATEST_DATE': None}
        self.db.result(msg)
        self.assertEqual(self.db.data['123']['LATEST'], 100)

    def test_discharge(self):
        msg = {'MRN': '123'}
        self.db.data['123'] = 'patient_info'
        self.db.discharge(msg)
        self.assertNotIn('123', self.db.data)

if __name__ == '__main__':
    unittest.main()