import os
from container_requester import ContainerRequester

class Converter:

    def __init__(self, container_requester=None):

        if container_requester is None:
            container_requester = ContainerRequester()

        self.worker_hostname = os.environ["LUNGMASK_CONVERTER_HOSTNAME"]
        self.worker_port = os.environ["LUNGMASK_CONVERTER_PORT"]
        self.convert_request_name = 'lungmask_convert_dcm_to_nifti'

        self.container_requester = container_requester

    def convert_dcm_to_nifti(self, source_directory):
        payload = {'source_dir': source_directory}

        response_dict = self.container_requester.send_request_to_worker(payload,
                                                                        self.worker_hostname,
                                                                        self.worker_port,
                                                                        self.convert_request_name)

        relative_nifti_filename = response_dict["filename"]

        return relative_nifti_filename
