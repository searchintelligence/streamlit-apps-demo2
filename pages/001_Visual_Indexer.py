from io import BytesIO, StringIO

import streamlit as st

import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

from utils import (
    convert_to_float_or_nan,
    load_file,
    TRANSFORMATIONS,
    USABLE_ROW_COUNT_LIMIT,
    ORDER_REVERSING_TRANSFORMATIONS,
    POLARITY_OPTIONS,
    get_column_name_raw,
    get_column_names_raw,
    MAX_INDEX_CELL_SCORE,
    MAX_INDEX_ROW_SCORE,
    create_unique_string
)

def load_excel_sheet(file_object: dict, sheet_name: str) -> pd.DataFrame:
    """
    Return a copy of the specified excel sheet as a pandas DataFrame

        Parameters:
            file_object (dict): A dict of pd.DataFrames representing excel worksheets
            sheet_name (str): The name of the excelw worksheet
        
        Returns:
            workhseet (pd.DataFrame): A pandas DataFrame copy of specified sheet
    """

    pass

if __name__ == "__main__":
    ############### Page config ###############
    st.set_page_config(
        page_title = "Visual Indexer",
        layout='wide'
    )

    st.cache_data
    def load_file_(uploaded_file: bytes) -> pd.DataFrame:
        """
        Wrapper for the load_file function in utils.py
        """
        
        return load_file(uploaded_file)
    

    st.title("Visual Indexer")

    ############### File upload ###############

    st.markdown("""---""") 
    st.subheader("File Upload")
    uploaded_file = st.file_uploader(label="Upload your **excel** or **csv** file.")

    with st.spinner("Loading file"):
        data_df_original = load_file(uploaded_file)
    
    if data_df_original is not None:
        data_df_using = data_df_original.copy()
    else:
        data_df_using = None
    

    ############### Charting ###############
    if data_df_using is not None:
        st.markdown("""---""")
        st.subheader("Data Transformations")        
        
        data_row_count = data_df_using.shape[0]

        with st.spinner("Creating charts"):
            usable_columns = []
            unusable_columns = []            
            for column_name in data_df_using.columns[1:]:
                data_df_using[column_name] =  data_df_using[column_name].apply(convert_to_float_or_nan)

                # determine whether column contains enought NON-na values
                if data_df_using[column_name].dropna().shape[0] >= USABLE_ROW_COUNT_LIMIT:
                    usable_columns.append(column_name)
                else:
                    unusable_columns.append(column_name)            

            column_count = len(usable_columns)
            row_count = len(TRANSFORMATIONS.keys())

            progress_text = "Applying Transformations for Charts"
            progress_bar = st.progress(0, text=progress_text)

            fig, ax = plt.subplots(nrows=row_count, ncols=column_count, figsize=(50, 50))
            
            axes = ax.ravel()
            ax_num = 0
            skews = {}
            kurts = {}
            for i, column_name in enumerate(usable_columns):
                progress_bar.progress((i + 1) / len(usable_columns), text=progress_text)
                column_data = data_df_using[column_name].dropna().astype(float)

                skews[column_name] = []
                kurts[column_name] = []
                
                for k, v in TRANSFORMATIONS.items():
                    #data_df_using[column].apply(v).hist(ax=axes[ax_num])
                    data = column_data.apply(v)
                    data.hist(ax=axes[ax_num])

                    data2 = data.dropna()
                    skewness_ = skew(data2)
                    kurtosis_ = kurtosis(data2)
                    axes[ax_num].set_title(f"{column_name}_{k}\nskew: {skewness_:.3f}, kurtosis: {kurtosis_:.3f}, obs: {len(data):,}, obs used: {len(data2):,}")
                    ax_num += 1

                    skews[column_name].append(skewness_)
                    kurts[column_name].append(kurtosis_)
            
            plt.tight_layout()

            if unusable_columns != []:
                st.write("Could not use the following column(s): " + ", ".join([f"'**{column_name}**'" for column_name in unusable_columns]))
            
            st.pyplot(fig)

    if data_df_using is not None:
        ############### Display raw data ###############

        st.write("---")
        st.subheader("Raw Data")
        
        st.write(data_df_using)

        ############### Display transformed data ###############

        st.write("---")
        st.subheader("Transformed Data (Automated)")

        transformations_to_use = {}
        for k, v in skews.items():
            # use transformation with lowest skew
            transformations_to_use[k] = list(TRANSFORMATIONS.keys())[np.argmin(np.abs(v))]

        #st.write(skews)
        #st.write(transformations_to_use)

        progress_text = "Applying Transformations for Index"
        progress_bar = st.progress(0, text=progress_text)

        columns_to_copy = [data_df_using.columns[0]] + usable_columns
        #st.write(columns_to_copy)

        data_df_using_transformed = data_df_using[columns_to_copy].copy()

        column_names_transformed = [data_df_using_transformed.columns[0]]
        for i, column_name in enumerate(data_df_using_transformed.columns[1:]):
            progress_bar.progress((i + 1)/len(data_df_using_transformed.columns[1:]), text=progress_text)            
            data_df_using_transformed[column_name] = data_df_using_transformed[column_name].apply(TRANSFORMATIONS[transformations_to_use[column_name]])
            column_names_transformed.append(f"{column_name}___{transformations_to_use[column_name]}")

        data_df_using_transformed.columns = column_names_transformed
        
        st.write(data_df_using_transformed)

        ############### Index Settings ###############

        st.write("---")
        st.subheader("Index Settings")

        column_names_raw = get_column_names_raw(data_df_using_transformed.columns)

        column_count = len(data_df_using_transformed.columns)        
        weights = dict(zip(column_names_raw, [100] * column_count))
        weights[""] = 0
        polarities = dict(zip(column_names_raw, ["higher is better"] * column_count))
        use_column = dict(zip(column_names_raw, [True] * column_count))

        #st.write(weights)
        #st.write(polarities)
        #st.write(use_column)

        with st.form("Settings"):
            column_widths = [0.225, 0.225, 0.225, 0.225, 0.10]
            header = st.columns(column_widths)
            header[0].subheader("Column")
            header[1].subheader("Transformation")
            header[2].subheader("Weight")
            header[3].subheader("Polarity")
            header[4].subheader("Use Column")

            st.write(usable_columns)

            for column_name in usable_columns:
                #st.write(column_name)
                row = st.columns(column_widths)
                #column_name_raw = get_column_name_raw(column_name)
                row[0].write(column_name)
                transformations_to_use[column_name] = row[1].selectbox(label=f"transformation_{column_name}", label_visibility="hidden", options=TRANSFORMATIONS.keys(), index=list(TRANSFORMATIONS.keys()).index(transformations_to_use[column_name]))
                weights[column_name] = row[2].slider(key=f"weight_{column_name}", label=f"weight", label_visibility="hidden", min_value=0, max_value=100, value=weights[column_name], step=1)
                polarities[column_name] = row[3].selectbox(label=f"polarity_{column_name}", label_visibility="hidden", options=POLARITY_OPTIONS, index=POLARITY_OPTIONS.index(polarities[column_name]))
                use_column[column_name] = row[4].checkbox(label=f"use_column_{column_name}", label_visibility="hidden", value=use_column[column_name])

            st.form_submit_button("Apply Settings")
        
        #st.write(weights)
        #st.write(polarities)
        #st.write(use_column)

        ############### Index Output ###############        

        st.write("---")
        #st.subheader("Index Output")

        # apply selected transformations
        columns_new = []        
        columns_new.append(data_df_using.iloc[:, 0])

        column_names_new = [data_df_using.columns[0]]
        for column_name in usable_columns:
            if use_column[column_name]:            
                #column_name_raw = get_column_name_raw(column_name)
                
                column_name_new = f"{column_name}___{transformations_to_use[column_name]}"
                column_names_new.append(column_name_new)
                
                column_data = data_df_using[column_name].apply(TRANSFORMATIONS[transformations_to_use[column_name]])
                columns_new.append(column_data)

        data_df_using_transformed = pd.concat(columns_new, axis=1)
        data_df_using_transformed.columns = column_names_new

        st.subheader("Transformed Data (User Selected)")
        st.write(data_df_using_transformed)

        # create index columns        
        #columns = [data_df_using_transformed.iloc[:, 0]]
        columns = [list(data_df_using_transformed.iloc[:, 0])]
        column_names = [data_df_using_transformed.columns[0]]
        #st.write(data_df_using_transformed.iloc[:, 0].shape)
        for column_name in data_df_using_transformed.columns[1:]:
            column_name_raw = get_column_name_raw(column_name)
            
            column_data = []
            col_max = data_df_using_transformed[column_name].max()
            col_min = data_df_using_transformed[column_name].min()
            col_range = col_max - col_min            

            inversion_required = transformations_to_use[column_name_raw] in ORDER_REVERSING_TRANSFORMATIONS
            higher_is_better = "higher" in polarities[column_name_raw].lower()

            #st.write(column_name, col_min, col_max, col_range, inversion_required, higher_is_better)
            
            for item in data_df_using_transformed[column_name]:
                value = MAX_INDEX_CELL_SCORE * ((item - col_min) / col_range)
                if (higher_is_better and inversion_required) or (not(higher_is_better) and not(inversion_required)):                    
                    value = MAX_INDEX_CELL_SCORE - value
                
                column_data.append(value)

            columns.append(column_data)
            column_names.append(column_name)
            #columns.append(pd.Series(column_data, name=column_name))
            #st.write(len(column_data), columns[-1].shape)

        #index_df = pd.concat(columns, axis=1)
        index_df = pd.DataFrame(np.array(columns).T, columns=column_names)
        #st.write([col.shape[0] for col in columns])
        #index_df = pd.DataFrame(columns, columns=[col.name for col in columns])        

        # scores
        weights_to_use = [weights[key] for key in weights.keys() if use_column[key]]
        max_score = np.sum(10 * np.array(weights_to_use))
        #st.write(max_score)
        #st.write(weights_to_use)
        #st.write(weights)
        
        row_scores = []
        for _, row in index_df.iterrows():
            sum = 0
            for column_name in row.index[1:]:                
                if (str(row[column_name]).lower() != 'nan') and str(row[column_name]).lower() != 'none':                    
                    column_name_raw = get_column_name_raw(column_name)
                    sum += float(row[column_name]) * weights[column_name_raw]                
            
            row_scores.append(sum)

        score_column_name = f'score/{MAX_INDEX_ROW_SCORE:,.0f}'

        index_df[score_column_name] = MAX_INDEX_ROW_SCORE * np.array(row_scores)/max_score
        index_df['rank'] = index_df[score_column_name].rank(ascending=False)
        
        st.subheader("Index Data")
        st.write(index_df)

             



