import psutil

from bs4 import BeautifulSoup 

import streamlit as st

st.set_page_config(
    page_title = 'Demo Apps'
)

st.title('Home Page')
st.sidebar.success('Select a page.')

cpu_count = psutil.cpu_count()

memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024

disk_space_total_gb = psutil.disk_usage('/').total / 1024 / 1024 / 1024
disk_space_used_gb = psutil.disk_usage('/').used / 1024 / 1024 / 1024
disk_space_free_gb = psutil.disk_usage('/').free / 1024 / 1024 / 1024

st.write(f'CPU count: {cpu_count:,}')
st.write(f'Ram size (GB): {memory_gb:.2f}')
st.write(f'Disk Space Total (GB): {disk_space_total_gb:.2f}')
st.write(f'Disk Space Used (GB): {disk_space_used_gb:.2f}')
st.write(f'Disk Space Free (GB): {disk_space_free_gb:.2f}')

