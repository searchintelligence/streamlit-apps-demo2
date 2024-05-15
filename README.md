# Streamlit Apps Demo
Some demo streamlit apps

[Apps can be found here](https://si-data-sl-apps-demo.streamlit.app/)

## 1) Visual Indexing Tool

A tool for creating indexes

Workflow:
1) Open the app [here](https://si-data-sl-apps-demo.streamlit.app/) and select "Visual Indexer" on the side bar
2) Upload file
    - only compatible with **csv** and **xlsx** files for now
    - csv files are assumed to have headers in the first row
    - for excel files a form is displayed asking for:
        -the worksheet name
        - the starting row of data
        - the  starting column of data
    - example files can be found [here](https://github.com/searchintelligence/streamlit-apps-demo2/tree/main/example_data)
3) Configure the index using the form in the **Index Settings** section. The following options are available for each variable.
    - **Transformation**: The transformation to be applied to the data
    - **Weight**: The weighting given to the variable in the index
    - **Polarity**: Determine whether a higher or lower score is preferred 
    - **Use Column**: Determine whether or not to include the column in the index
4) Click the **Apply Settings** button to submit the form and update the index output
5) Results can be downloaded directly from the displayed data frames

### Todo
1) Add option to download a full excel file with all of the data (including methodology)
2) Switch charts to Bokeh/Altair
    - Current matplotlib charts don't have high enough DPI, turning DPI up makes the image file size too large
3) Refactor the code into separate functions and .py files
4) Format data to fewer decimal places
    - Add option for user to adjust formatting
