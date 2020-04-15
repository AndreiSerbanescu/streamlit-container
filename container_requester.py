import requests as req
from time import time, sleep
import os
import json


class ContainerRequester:

    def send_request_to_worker(self, payload, worker_hostname, worker_port, request_name):

        ready = self.wait_until_ready(worker_hostname)

        if not ready:
            print("{} not ready".format(worker_hostname), flush=True)
            raise Exception("{} not ready".format(worker_hostname))

        response = req.get('http://{}:{}/{}'.format(worker_hostname, worker_port, request_name), params=payload)

        print("Got response text", response.text)
        response_dict = json.loads(response.text)

        return response_dict


    def wait_until_ready(self, hostname):
        data_share_path = os.environ['DATA_SHARE_PATH']

        backoff_time = 0.5
        wait_time = 10

        curr_time = time()
        finish_time = curr_time + wait_time

        while curr_time < finish_time:

            print("Waiting for {} to start".format(hostname))
            # log_info("Waiting for {} to start".format(hostname))

            if os.path.exists("{}/{}_ready.txt".format(data_share_path, hostname)):
                # component ready
                return True

            sleep(10 * backoff_time)
            curr_time = time()

        print("Component not ready")
        # log_info("Component not ready")
        return False
