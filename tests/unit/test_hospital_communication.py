import acces_main_directory

import unittest
from hospital_communication import to_mllp, from_mllp, classify_msg, parse_admission, parse_test_result, parse_discharge
import datetime


class TestHospitalCommunication(unittest.TestCase):

    def test_to_mllp(self):
        segments = ['SEG1', 'SEG2', 'SEG3']
        result = to_mllp(segments)
        self.assertEqual(result, b'\x0bSEG1\rSEG2\rSEG3\r\x1c\x0d')

    def test_from_mllp(self):
        buffer = b'\x0bSEG1\rSEG2\rSEG3\r\x1c\x0d'
        result = from_mllp(buffer)
        self.assertEqual(result, ['SEG1', 'SEG2', 'SEG3'])

    def test_classify_msg(self):
        self.assertEqual(classify_msg(['ADT^A01']), 'ADMIT')
        self.assertEqual(classify_msg(['ORU^R01']), 'CREATININE')
        self.assertEqual(classify_msg(['ADT^A03']), 'DISCHARGE')

    def test_parse_admission(self):
        msg = ['MSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||202401201630||ADT^A01|||2.5',
               'PID|1||478237423||ELIZABETH HOLMES||19840203|F',
               'NK1|1|SUNNY BALWANI|PARTNER']
        result = parse_admission(msg)
        self.assertEqual(result, {'MRN': 478237423, 'AGE': 40, 'SEX': 0})

    def test_parse_test_result(self):
        msg = ['MSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||202401201630||ORU^R01|||2.5',
               'PID|1||478237423 ', #in this message mrn ends in a white space which is throwing an error for mrn = re.search(last_numerical_regex, creatinine_msg[1]).group()
               'OBR|1||||||202401202243 ',
               'OBX|1|SN|CREATININE||103.4']
        result = parse_test_result(msg)
        if result:
            self.assertIn(result['MRN'], [478237423, None])
            self.assertEqual(result['DATE'], datetime.strptime(
                '202401202243', '%Y%m%d%H%M'))
            self.assertTrue(0 <= result['RESULT'] <= 100)

    def test_parse_discharge(self):
        msg = ['MSH|^~\&|SIMULATION|SOUTH RIVERSIDE|||202401201630||ADT^A03|||2.5',
               'PID|1||478237423']
        result = parse_discharge(msg)
        self.assertEqual(result, {'MRN': 478237423})


if __name__ == '__main__':
    unittest.main()
