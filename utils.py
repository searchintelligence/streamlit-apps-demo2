from io import BytesIO

import numpy as np
import pandas as pd

import streamlit as st

# minimum acceptable percentage of NON-na values in column
USABLE_ROW_COUNT_LIMIT = 0.6

TRANSFORMATIONS = {
    "raw": lambda x: x,    
    #"log": lambda x: np.log(x) if x > 0 else np.nan,    
    "log": lambda x: np.log(x + 0.000001),
    "inverse": lambda x: 1/x if x != 0 else np.nan,    
    "square_root": lambda x: np.sqrt(x) if x > 0 else np.nan,    
    #"eigth_root": lambda x: x ** 0.125 if x > 0 else np.nan,    
    "squared": lambda x: x ** 2,
    #"power_four": lambda x: x ** 4
}

ORDER_REVERSING_TRANSFORMATIONS = {"inverse"}

POLARITY_OPTIONS = [
    'higher is better',
    'lower is better'
]

VALID_FILE_EXTENSIONS = [
    "csv",
    "xlsx"
]

MAX_INDEX_CELL_SCORE = 10
MAX_INDEX_ROW_SCORE = 100

def load_file_OLD(uploaded_file: bytes) -> pd.DataFrame:
    """
    Return a copy of the specified excel sheet as a pandas DataFrame

        Parameters:
            uploaded_file (bytes):            
        
        Returns:
            data_df (pd.DataFrame):
    """

    if uploaded_file is not None:
        file_extention = uploaded_file.name.split(".")[-1]
    else:
        file_extention = ""

    if file_extention == "":
        # no data uploaded
        data_df = None
    elif file_extention not in VALID_FILE_EXTENSIONS:
        # unsupported file type
        st.write(f"Unsupported file type '{file_extention}'. Please upload an excel or csv file.")
        data_df = None
    else:
        # load csv or excel file
        try:
            if file_extention == "csv":
                data_df = pd.read_csv(BytesIO(uploaded_file.read()))
            else:
                # get excel worksheet names
                workbook = pd.read_excel(BytesIO(uploaded_file.read()), sheet_name=None)
                sheet_name = st.selectbox(label="Select a worksheet", options=workbook.keys())

                # load excel worksheet
                if sheet_name != "":
                    data_df = workbook[sheet_name]

                    # remove empty rows
                    row = 0
                    while True:                            
                        if data_df.iloc[row].value_counts().shape[0] != 0:
                            break
                        
                        row += 1

                    column_names = list(data_df.iloc[row])
                    data_df = data_df.iloc[row + 1:].copy()
                    data_df.columns = column_names

                    if len(data_df.columns) != len(set(data_df.columns)):
                        # incorrectly formatted worksheet
                        st.write(f"Unable to read data from '{sheet_name}' worksheet. Incorrectly formatted data.")
                        data_df = None
                else:
                    data_df = None
        except AttributeError as e:
            st.write("Exception raised while loading file.")
            st.write(e)
            data_df = None

    return data_df

def load_file(uploaded_file: bytes) -> pd.DataFrame:
    """
    Return a copy of the specified excel sheet as a pandas DataFrame

        Parameters:
            uploaded_file (bytes):            
        
        Returns:
            data_df (pd.DataFrame):
    """

    if uploaded_file is not None:
        file_extention = uploaded_file.name.split(".")[-1]
    else:
        file_extention = ""

    if file_extention == "":
        # no data uploaded
        data_df = None
    elif file_extention not in VALID_FILE_EXTENSIONS:
        # unsupported file type
        st.write(f"Unsupported file type '{file_extention}'. Please upload an excel or csv file.")
        data_df = None
    else:
        # load csv or excel file
        try:
            if file_extention == "csv":
                data_df = pd.read_csv(BytesIO(uploaded_file.read()))
            else:
                # get excel worksheet names
                workbook = pd.read_excel(BytesIO(uploaded_file.read()), sheet_name=None)

                with st.form("Worksheet Selection"):
                    column_widths = [0.8, 0.1, 0.1]
                    header = st.columns(column_widths)
                    header[0].subheader("Worksheet Name")
                    header[1].subheader("Start Row")
                    header[2].subheader("Start Column")

                    row = st.columns(column_widths)                    
                    sheet_name = row[0].selectbox(label="Select a worksheet", options=workbook.keys())
                    row_number = row[1].slider(label=f"row number", label_visibility="hidden", min_value=1, max_value=50, value=1, step=1)
                    column_number = row[2].slider(label=f"column number", label_visibility="hidden", min_value=1, max_value=50, value=1, step=1)
                    st.write(row_number)
                    
                    st.form_submit_button("Load Data")

                # load excel worksheet
                if sheet_name != "":
                    data_df = workbook[sheet_name]                    
                    column_names = list(data_df.iloc[row_number - 2])[column_number - 1:]                    

                    column_names_adjusted = []
                    for column_name in column_names:
                        column_name_adjusted = create_unique_string(column_name, column_names_adjusted)                        
                        column_names_adjusted.append(column_name_adjusted)
                    
                    data_df = data_df.iloc[row_number - 1:, column_number - 1:].copy()
                    data_df.columns = column_names_adjusted

                    if len(data_df.columns) != len(set(data_df.columns)):
                        # incorrectly formatted worksheet
                        st.write(f"Unable to read data from '{sheet_name}' worksheet. Incorrectly formatted data.")
                        data_df = None
                else:
                    data_df = None
        except AttributeError as e:
            st.write("Exception raised while loading file.")
            st.write(e)
            data_df = None

    return data_df

def convert_to_float_or_nan(value: [int, float, str]):
    """
    Convert value to float or return np.nan

        Parameters:
            value (int|float|string)
        
        Returns:
            value_out (float)

    """
    try:
        value_out = float(value)
    except ValueError:
        value_out = np.nan

    return value_out

def get_column_name_raw(column_name_in: str, splitter="___") -> str:
    """
        Splits an input string on the specified splitter and returns the first n-1 elements

        Parameters:
            column_name_in (str)
            splitter (str): string of characters used to split input string
        
        Returns:
            column_name_out (str): the first n-1 elements of input string when split on splitter


    """
    
    column_name_out = "".join(column_name_in.split(splitter)[:-1])
    
    return column_name_out

def get_column_names_raw(column_names_in: list[str]) -> list[str]:
    """
    Generates "raw" column names from column names which include transformation as a postfix

        Parameters:
            column_names_in (list[str])
        
        Returns:
            column_names_out (list[str]): a list of column names with the postfix removed

    """
    column_names_out = []
    for column_name in column_names_in:
        column_names_out.append(get_column_name_raw(column_name))

    return column_names_out

def create_unique_string(text: str, disallowed_strings: list[str], unique_postfix="-") -> str:
    if text not in disallowed_strings:
        return text
    
    text = f"{text}{unique_postfix}"
    return create_unique_string(text, disallowed_strings)
