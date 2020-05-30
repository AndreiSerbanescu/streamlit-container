import logging
import sys
import os
import subprocess as sb
import time
from threading import get_ident

def get_unique_id():
    return str(time.time()) + "-" + str(get_ident())

def setup_logging():
    file_handler = logging.FileHandler("../log.log")
    stream_handler = logging.StreamHandler(sys.stdout)

    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    # stream_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    stream_handler.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s"))

    logging.basicConfig(
        level=logging.DEBUG, # TODO level=get_logging_level(),
        # format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            file_handler,
            stream_handler
        ]
    )

def mark_yourself_ready():
    hostname = os.environ['HOSTNAME']
    data_share_path = os.environ['DATA_SHARE_PATH']

    ready_directory = os.path.join(data_share_path, "containers_ready")
    os.makedirs(ready_directory, exist_ok=True)

    ready_filepath = os.path.join(ready_directory, f"{hostname}_ready.txt")
    cmd = f"touch {ready_filepath}"

    logging.info("Marking as ready")
    sb.call([cmd], shell=True)

def log_info(*msg):
    logging.info(__get_print_statement(*msg))

def log_debug(*msgs):
    logging.debug(__get_print_statement(*msgs))

def log_warning(*msg):
    logging.warning(__get_print_statement(*msg))

def log_error(*msg):
    logging.error(__get_print_statement(*msg))

def log_critical(*msg):
    logging.critical(__get_print_statement(*msg))

def __get_print_statement(*msgs):
    if type(msgs) == str:
        return msgs

    print_statement = ""
    for msg in msgs:
        print_statement = print_statement + str(msg) + " "
    return print_statement
