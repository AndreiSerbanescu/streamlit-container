import os
import requests as req
from time import time
import numpy as np
import json

def lungmask_segment(source_dir, model_name='R231CovidWeb'):

    if os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE":
        return __docker_lungmask_segment(source_dir, model_name=model_name)

    return __host_lungmask_segment(source_dir, model_name=model_name)

def __host_lungmask_segment(source_dir, model_name):

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

def __docker_lungmask_segment(source_dir, model_name):
    payload = {'source_dir': source_dir, 'model_name': model_name}

    ready = __wait_until_ready(os.environ['LUNGMASK_HOSTNAME'])

    if not ready:
        # log_critical("Lungmask not ready")
        print("Lungmask not ready", flush=True)
        raise Exception("Lungmask not ready")

    hostname = os.environ['LUNGMASK_HOSTNAME']
    port = os.environ['LUNGMASK_PORT']
    service_name = 'lungmask_segment'

    response = req.get('http://{}:{}/{}'.format(hostname, port, service_name), params=payload)

    # json_resp = response.text
    # array = json.loads(json_resp)
    # np_array = np.asarray(array)

    print("Got response text", response.text)

    response_dict = json.loads(response.text)

    rel_seg_path       = response_dict["segmentation"]
    rel_input_nda_path = response_dict["input_nda"]
    spx, spy, spz      = response_dict["spacing"]

    data_share = os.environ["DATA_SHARE_PATH"]

    segmentation_path = os.path.join(data_share, rel_seg_path)
    input_nda_path    = os.path.join(data_share, rel_input_nda_path)

    print("load np array from", segmentation_path)
    segmentation = np.load(segmentation_path)
    print("load np array from", input_nda_path)
    input_nda    = np.load(input_nda_path)

    return segmentation, input_nda, spx, spy, spz

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
