try:
    import streamlit
except ImportError:
    pass

import os

class DownloadDisplayer:

    def __init__(self, fileserver_address=None, fileserver_port=None, streamlit_wrapper=None):

        self.st = streamlit if streamlit_wrapper is None else streamlit_wrapper

        self.fs_address = fileserver_address if fileserver_address is not None else os.environ["FILESERVER_ADDRESS"]

        self.fs_port = fileserver_port if fileserver_port is not None else os.environ["FILESERVER_PORT"]

    def display(self, resource_name, display_name="Resource"):
        file_server_url = f"http://{self.fs_address}:{self.fs_port}/{resource_name}"
        html = f'<a href="{file_server_url}" target="_blank">Download {display_name}</a>'
        self.st.markdown(html, unsafe_allow_html=True)

class DownloadDisplayerReport:

    def __init__(self, fileserver_address=None, fileserver_port=None, streamlit_wrapper=None):

        self.use_original_streamlit = streamlit_wrapper is None
        self.st = streamlit if streamlit_wrapper is None else streamlit_wrapper
        self.fs_address = fileserver_address if fileserver_address is not None else os.environ["FILESERVER_ADDRESS"]

        self.fs_port = fileserver_port if fileserver_port is not None else os.environ["FILESERVER_PORT"]

    def display(self, resource_name, display_name="Resource"):
        file_server_url = f"http://{self.fs_address}:{self.fs_port}/{resource_name}"
        download_hyperlink = f"[Click here to download {display_name}]({file_server_url})"

        if self.use_original_streamlit:
            self.st.markdown(download_hyperlink)
        else:
            self.st.markdown_hyperlink(download_hyperlink, display_name, file_server_url)

