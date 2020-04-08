import os
import requests as req
from time import time
import numpy as np
import json
import SimpleITK as sitk


# for nifti files source is of type: /path/to/file.nii.gz
def ct_muscle_segment_nifti(source_file):

    assert os.environ.get("ENVIRONMENT", "").upper() != "DOCKERCOMPOSE"

    return __ct_muscle_segment_nifti(source_file)


# for dcm files source is of type: /path/to/directory
def ct_muscle_segment_dcm(source_directory):
    assert os.environ.get("ENVIRONMENT", "").upper() != "DOCKERCOMPOSE"

    nifti_filename = __converter_convert_dcm_to_nifti(source_directory)
    return __ct_muscle_segment_nifti(nifti_filename)


def __converter_convert_dcm_to_nifti(source_directory):
    payload = {'source_dir': source_directory}
    ready = __wait_until_ready(os.environ['LUNGMASK_CONVERTER_HOSTNAME'])

    if not ready:
        print("Lungmask converter not ready", flush=True)
        raise Exception("Lungmask converter not ready")

    hostname = os.environ['LUNGMASK_CONVERTER_HOSTNAME']
    port = os.environ['LUNGMASK_CONVERTER_PORT']
    request_name = 'lungmask_convert_dcm_to_nifti'

    response = req.get('http://{}:{}/{}'.format(hostname, port, request_name), params=payload)

    print("Got response text", response.text)
    response_dict = json.loads(response.text)

    rel_fn_path = response_dict["filename"]
    data_share = os.environ["DATA_SHARE_PATH"]

    nifti_filename = os.path.join(data_share, rel_fn_path)

    return nifti_filename

def __ct_muscle_segment_nifti(source_file):
    assert __is_nifti(source_file)

    payload = {'source_file': source_file}
    ready = __wait_until_ready(os.environ['CT_MUSCLE_SEG_HOSTNAME'])

    if not ready:
        print("CT Muscle Segment not ready", flush=True)
        raise Exception("CT Muscle Segment not ready")

    hostname = os.environ['CT_MUSCLE_SEG_HOSTNAME']
    port = os.environ['CT_MUSCLE_SEG_PORT']
    request_name = 'ct_segment_muscle'

    response = req.get('http://{}:{}/{}'.format(hostname, port, request_name), params=payload)

    print("Got response text", response.text)
    response_dict = json.loads(response.text)

    rel_seg_path = response_dict["segmentation"]
    data_share = os.environ["DATA_SHARE_PATH"]

    segmentation_path = os.path.join(data_share, rel_seg_path)

    print("reading muscle segmentation from", segmentation_path)
    segmentation = __read_nifti_image(segmentation_path)

    return segmentation

def __read_nifti_image(path):
    reader = sitk.ImageFileReader()
    reader.SetImageIO("NiftiImageIO")
    reader.SetFileName(path)
    image = reader.Execute()

    return image

def __is_nifti(filepath):

    _, file = os.path.split(filepath)

    file_exts = file.split('.')
    if len(file_exts) < 3:
        return False

    nii = file_exts[len(file_exts) - 2]
    gz  = file_exts[-1]

    return nii == "nii" and gz == "gz"

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
    request_name = 'lungmask_segment'

    response = req.get('http://{}:{}/{}'.format(hostname, port, request_name), params=payload)

    print("Got response text", response.text)

    response_dict = json.loads(response.text)

    rel_seg_path       = response_dict["segmentation"]
    rel_input_nda_path = response_dict["input_nda"]
    spx, spy, spz      = response_dict["spacing"]

    data_share = os.environ["DATA_SHARE_PATH"]

    # TODO delete volume files after reading them

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
