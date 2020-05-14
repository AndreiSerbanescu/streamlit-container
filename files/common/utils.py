import logging
import sys
import os
import subprocess as sb
import time
import random

def get_unique_id():
    return str(time.time()) + "-" + str(random.randint(0, 10000000))

def setup_logging():
    file_handler = logging.FileHandler("../log.log")
    stream_handler = logging.StreamHandler(sys.stdout)

    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    stream_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

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
    cmd = "touch {}/{}_ready.txt".format(data_share_path, hostname)

    logging.info("Marking as ready")
    sb.call([cmd], shell=True)

def log_info(*msg):
    logging.info(__get_print_statement(*msg))

def log_debug(*msgs):
    logging.debug(__get_print_statement(*msgs))

def log_critica(*msg):
    logging.critical(__get_print_statement(*msg))

def log_warning(*msg):
    logging.warning(__get_print_statement(*msg))

def log_critical(*msg):
    logging.critical(__get_print_statement(*msg))

def __get_print_statement(*msgs):
    if type(msgs) == str:
        return msgs

    print_statement = ""
    for msg in msgs:
        print_statement = print_statement + str(msg) + " "
    return print_statement