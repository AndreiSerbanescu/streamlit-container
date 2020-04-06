import os
import requests as req
from time import time
import numpy as np
import json

def lungmask_segment(source_dir, model_name='R231CovidWeb'):

    payload = {'source_dir': source_dir, 'model_name': model_name}

    ready = __wait_until_ready(os.environ['LUNGMASK_HOSTNAME'])

    if not ready:
        # log_critical("Lungmask not ready")
        print("Lungmask not ready", flush=True)
        raise Exception("Lungmask not ready")

    hostname = os.environ['LUNGMASK_HOSTNAME']
    port = os.environ['LUNGMASK_PORT']
    service_name = 'please_segment'

    response = req.get('http://{}:{}/{}'.format(hostname, port, service_name), params=payload)

    # json_resp = response.text
    # array = json.loads(json_resp)
    # np_array = np.asarray(array)

    relative_save_path = response.text
    data_share = os.environ["DATA_SHARE_PATH"]
    save_path = os.path.join(data_share, relative_save_path)

    print("load np array from", save_path)

    return np.load(save_path)


def __wait_until_ready(hostname):
    data_share_path = os.environ['DATA_SHARE_PATH']

    backoff_time = 0.5
    wait_time = 10

    curr_time = time()
    finish_time = curr_time + wait_time

    while curr_time < finish_time:

        print("Waiting for {} to start".format(hostname))
        #log_info("Waiting for {} to start".format(hostname))

        if os.path.exists("{}/{}_ready.txt".format(data_share_path, hostname)):
            #component ready
            return True

        sleep(10 * backoff_time)
        curr_time = time()

    print("Component not ready")
    #log_info("Component not ready")
    return False
