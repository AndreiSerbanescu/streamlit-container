import os
from workers.converter import Converter
import workers.nifti_reader as nifti_reader

class CovidDetector:

    def __init__(self, container_requester):
        self.container_requester = container_requester

        self.worker_hostname = os.environ["COVID_DETECTOR_HOSTNAME"]
        self.worker_port     = os.environ["COVID_DETECTOR_PORT"]
        self.request_name = "covid_detector_nifti"

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


        rel_attention_volume_path = response_dict["auxiliary_volume"]
        rel_detection_volume_path = response_dict["detection_volume"]

        data_share = os.environ["DATA_SHARE_PATH"]

        attention_volume_path = os.path.join(data_share, rel_attention_volume_path)
        detection_volume_path = os.path.join(data_share, rel_detection_volume_path)

        if filepath_only:
            return attention_volume_path, detection_volume_path

        attention_volume = nifti_reader.read_nifti_image(attention_volume_path)
        detection_volume = nifti_reader.read_nifti_image(detection_volume_path)

        return attention_volume, detection_volume
