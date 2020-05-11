import streamlit as st
import os

class DownloadDisplayer():

    def __init__(self, fileserver_address=None, fileserver_port=None):
        self.fs_address = fileserver_address if fileserver_address is not None else os.environ["FILESERVER_ADDRESS"]

        self.fs_port = fileserver_port if fileserver_port is not None else os.environ["FILESERVER_PORT"]

    def display(self, resource_name, display_name="Resource"):
        file_server_url = f"http://{self.fs_address}:{self.fs_port}/{resource_name}"
        html = f'<a href="{file_server_url}" target="_blank">Download {display_name}</a>'
        st.markdown(html, unsafe_allow_html=True)

