from workers.converter import Converter
import os
import SimpleITK as sitk
import workers.nifti_reader as nifti_reader

class CTMuscleSegmenter:

    def __init__(self, container_requester):
        self.worker_hostname = os.environ["CT_MUSCLE_SEG_HOSTNAME"]
        self.worker_port = os.environ["CT_MUSCLE_SEG_PORT"]
        self.segment_muscle_request_name = "ct_segment_muscle"

        self.container_requester = container_requester
        self.converter = Converter(self.container_requester)

    def segment_nifti(self, source_file, filepath_only=False):
        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

        return self.__segment_nifti(source_file, filepath_only=filepath_only)

    def segment_dcm(self, source_directory, filepath_only=False):
        assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

        nifti_filename = self.converter.convert_dcm_to_nifti(source_directory)
        return self.__segment_nifti(nifti_filename, filepath_only=filepath_only)


    def __segment_nifti(self, source_file, filepath_only=False):
        # assert __is_nifti(source_file)

        payload         = {'source_file': source_file}

        print("filepath only ", filepath_only)

        response_dict = self.container_requester.send_request_to_worker(payload,
                                                                        self.worker_hostname,
                                                                        self.worker_port,
                                                                        self.segment_muscle_request_name)

        rel_seg_path = response_dict["segmentation"]
        data_share = os.environ["DATA_SHARE_PATH"]

        segmentation_path = os.path.join(data_share, rel_seg_path)
        abs_source_file   = os.path.join(data_share, source_file)

        if filepath_only:
            return segmentation_path, abs_source_file

        print("reading muscle segmentation from", segmentation_path)
        segmentation = nifti_reader.read_nifti_image(segmentation_path)
        original     = nifti_reader.read_nifti_image(abs_source_file)

        return segmentation, original
