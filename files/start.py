import subprocess as sb
from threading import Thread
from file_server.file_server import start_file_server

def start_streamlit():

    streamlit_cmd = "streamlit run /app/src/main.py"
    sb.call([streamlit_cmd], shell=True)

if __name__ == "__main__":

    streamlit_thread = Thread(target=start_streamlit)
    fserver_thread = Thread(target=start_file_server)

    streamlit_thread.start()
    fserver_thread.start()
