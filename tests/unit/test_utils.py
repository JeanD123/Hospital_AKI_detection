import acces_main_directory

import unittest
import pandas as pd
from utils import read_file, cast_types, pivot_rows



class TestUtils(unittest.TestCase):
    """
    A class that contains unit tests for the utility functions in the 'utils' module.
    """

    def test_cast_types(self):
        """
        Test that the 'cast_types' function correctly changes column types in a DataFrame.
        """
        df = pd.DataFrame({
            'creatinine_date': ['2022-01-01'],
            'creatinine_result': ['1.23']
        })
        df = cast_types(df)
        self.assertEqual(df['creatinine_date'].dtype, 'datetime64[ns]')
        self.assertEqual(df['creatinine_result'].dtype, 'float')



if __name__ == '__main__':
    unittest.main()
