# this file is for data handling
import pandas as pd
import csv

def read_file(path: str) -> pd.DataFrame:
    """
    Reading in the data file and constructing a data set.

    Parameters:
    - path (str): The path to the input file.

    Returns:
    - pd.DataFrame: The resulting dataframe.
    """
    data = []

    with open(path, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader, None)
        
        for row in csv_reader:
            # Create a dictionary for each row
            row_dict = {}
            
            # Fill the dictionary with the values, handling mismatch in column counts
            for col_num, value in enumerate(row):
                row_dict[header[col_num]] = value
            data.append(row_dict)

    df = pd.DataFrame(data)
    return df

def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Changing some of the column values type. For example, making age an int
    and sex a dummy variable.

    Parameters:
    - df (pd.DataFrame): The input dataframe as read in from the csv file.

    Returns:
    - pd.DataFrame: The dataframe with the new types.
    """
    for col in df.columns:
        if col.startswith('creatinine_date'):
            df[col] = pd.to_datetime(df[col])
        elif col.startswith('creatinine_result'):
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float')
    return df

def pivot_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot the rows of this dataframe into columns.

    Parameters:
    - df (pd.DataFrame): The input dataframe.

    Returns:
    - pd.DataFrame: The resulting pivoted dataframe.
    """
    df_long = pd.melt(df, id_vars=['mrn'], var_name='variable', value_name='value')
    df_long[['type', 'number']] = df_long['variable'].str.split('_', n=-1, expand=True).iloc[:, -2:]
    df_pivot = df_long.pivot_table(index=['mrn', 'number'], columns='type', values='value', aggfunc='first').reset_index()
    df_pivot = df_pivot.drop('number', axis='columns')
    df_pivot.columns = ['MRN', 'DATE', 'RESULT']
    df_pivot['DATE'] = pd.to_datetime(df_pivot['DATE'])
    df_pivot['MRN'] = df_pivot['MRN'].astype('int')
    return df_pivot