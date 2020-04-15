import os
import numpy as np


class LungmaskSegmenter:

    def __init__(self, container_requester):
        self.worker_hostname = os.environ['LUNGMASK_HOSTNAME']
        self.worker_port = os.environ['LUNGMASK_PORT']
        self.segment_request_name = 'lungmask_segment'

        self.container_requester = container_requester


    def segment(self, source_dir, model_name='R231CovidWeb', filepath_only=False):

        if os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE":
            return self.__docker_segment(source_dir, model_name=model_name, filepath_only=filepath_only)

        return self.__host_segment(source_dir, model_name=model_name)



    def __host_segment(self, source_dir, model_name):

        from lungmask import lungmask
        from lungmask import utils
        import SimpleITK as sitk

        model = lungmask.get_model('unet', model_name)
        input_image = utils.get_input_image(source_dir)
        input_nda = sitk.GetArrayFromImage(input_image)
        print(input_nda.shape)

        spx, spy, spz = input_image.GetSpacing()
        segmentation = lungmask.apply(input_image, model, force_cpu=False, batch_size=20, volume_postprocessing=False)

        return segmentation, input_nda, spx, spy, spz

    def __docker_segment(self, source_dir, model_name, filepath_only):

        payload = {'source_dir': source_dir, 'model_name': model_name}

        response_dict = self.container_requester.send_request_to_worker(payload,
                                                                        self.worker_hostname,
                                                                        self.worker_port,
                                                                        self.segment_request_name)

        rel_seg_path       = response_dict["segmentation"]
        rel_input_nda_path = response_dict["input_nda"]
        spx, spy, spz      = response_dict["spacing"]

        data_share = os.environ["DATA_SHARE_PATH"]

        # TODO delete volume files after reading them

        segmentation_path = os.path.join(data_share, rel_seg_path)
        input_nda_path    = os.path.join(data_share, rel_input_nda_path)

        if filepath_only:
            return segmentation_path, input_nda_path, spx, spy, spz

        print("load np array from", segmentation_path)
        segmentation = np.load(segmentation_path)
        print("load np array from", input_nda_path)
        input_nda    = np.load(input_nda_path)

        return segmentation, input_nda, spx, spy, spz