import requests as req
from time import time, sleep
import os
import json
from exceptions.workers import *


class ContainerRequester:

    def send_request_to_worker(self, payload, worker_hostname, worker_port, request_name):

        ready = self.wait_until_ready(worker_hostname)

        if not ready:
            print("{} not ready".format(worker_hostname), flush=True)
            raise WorkerNotReadyException(worker_hostname)

        try:
            response = req.get('http://{}:{}/{}'.format(worker_hostname, worker_port, request_name), params=payload)
        except req.exceptions.ConnectionError:
            print(f"Worker {worker_hostname} didn't respond")
            raise WorkerFailedException(worker_hostname)
        except Exception as e:
            print(F"WARNING: Other {worker_hostname} exception {e}")
            raise WorkerFailedException(worker_hostname)

        if response.status_code != 200:
            print("Got nonsuccessful response code")
            raise WorkerFailedException(worker_hostname)

        print("Got response text", response.text)
        response_dict = json.loads(response.text)

        return response_dict


    def wait_until_ready(self, hostname):
        data_share_path = os.environ['DATA_SHARE_PATH']

        backoff_time = 0.5
        wait_time = 10

        curr_time = time()
        finish_time = curr_time + wait_time
        ready_path = os.path.join(data_share_path, "containers_ready", f"{hostname}_ready.txt")

        while curr_time < finish_time:

            print("Waiting for {} to start".format(hostname))
            # log_info("Waiting for {} to start".format(hostname))

            if os.path.exists(ready_path):
                # component ready
                return True

            sleep(10 * backoff_time)
            curr_time = time()

        print("Component not ready")
        # log_info("Component not ready")
        return False
