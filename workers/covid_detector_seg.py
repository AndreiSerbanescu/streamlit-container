import os
from workers.converter import Converter

class CovidDetectorSeg:

    def __init__(self, container_requester):
        self.container_requester = container_requester

        self.worker_hostname = os.environ["COVID_DETECTOR_SEG_HOSTNAME"]
        self.worker_port     = os.environ["COVID_DETECTOR_SEG_PORT"]
        self.request_name = "covid_detector_seg_nifti"

        self.converter = Converter(self.container_requester)

    def generate_detection_and_attention_maps_nifti(self, source_file, filepath_only):

        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"
        return self.__generate_maps(source_file, filepath_only=filepath_only)

    def generate_detection_and_attention_maps_dcm(self, source_file, filepath_only):
        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

        nifti_filename = self.converter.convert_dcm_to_nifti(source_file)
        return self.__generate_maps(nifti_filename, filepath_only=filepath_only)

    def __generate_maps(self, source_file, filepath_only):
        payload = {"source_file": source_file}

        response_dict = self.container_requester.send_request_to_worker(payload,
                                                                        self.worker_hostname,
                                                                        self.worker_port,
                                                                        self.request_name)

        if filepath_only:
            return "" # TODO return filenames

        return "" # TODO return actual images
        # report_path = response_dict["fat_report"]
        # print("Report path")
        #
        # return report_csv