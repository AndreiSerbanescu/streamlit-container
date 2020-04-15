import os
import requests as req
from time import time, sleep
import numpy as np
import json
import SimpleITK as sitk
import csv
import subprocess as sb
import math
from shutil import copyfile
from threading import Thread
from queue import Queue

# ALL PATHS INPUTTED ARE RELATIVE TO $DATA_SHARE_PATH


# TODO split into different files

def ct_fat_measure_nifti(source_file, filepath_only=False, split=False):
    assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

    assert __is_nifti(source_file)
    return __ct_fat_measure(source_file, "ct_visceral_fat_nifti", filepath_only=filepath_only)


def ct_fat_measure_dcm(source_file, filepath_only=False, split=False):
    assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

    # if split:
    #     return __ct_fat_measure_dcm_split(source_file, filepath_only=filepath_only)

    return __ct_fat_measure_dcm_single(source_file, filepath_only=filepath_only)

def  __ct_fat_measure_dcm_single(source_file, filepath_only):
    nifti_filename = __converter_convert_dcm_to_nifti(source_file)
    return __ct_fat_measure(nifti_filename, "ct_visceral_fat_nifti", filepath_only=filepath_only)

# def __ct_fat_measure_dcm_split(source_file, filepath_only):
#
#
#     #TODO fix infinite threads
#     dcm_files = sorted(os.listdir(source_file))
#     file_no = len(dcm_files)
#     split_no = 4
#     file_no_in_split = math.ceil(file_no / split_no)
#
#     intervals = []
#     for i in range(split_no):
#         intervals.append((i * file_no_in_split, min((i + 1) * file_no_in_split, file_no)))
#
#     data_share = os.environ["DATA_SHARE_PATH"]
#     unique_file = "streamlit-fat-measure-split_" + str(time())
#
#     base_dir = os.path.join(data_share, unique_file)
#     os.makedirs(unique_file, exist_ok=False)
#
#     split_dirs = []
#     for i in range(split_no):
#         interval = intervals[i]
#         sub_dir = str(i)
#         split_dir = os.path.join(base_dir, sub_dir)
#
#         os.makedirs(split_dir, exist_ok=False)
#
#         split_dirs.append(split_dir)
#
#         __ct_fat_measure_move_files(source_file, interval, split_dir)
#
#     threads = []
#
#     queue = Queue()
#
#     for i in range(len(split_dirs)):
#         split_dir = split_dirs[i]
#
#         def fat_measure_wrapper(split_dir, id):
#             csv_report = __ct_fat_measure_dcm_split(split_dir, filepath_only=False)
#             return csv_report, id
#
#         thread = Thread(target=lambda q: q.put(fat_measure_wrapper(split_dir, i)),
#                         args=(queue,))
#
#         threads.append(thread)
#         thread.start()
#
#     for thread in threads:
#         thread.join()
#
#     csv_reports = {}
#     while not queue.empty():
#         csv_report, id = queue.get()
#         csv_reports[id] = csv_reports
#
#
#     agg_report = __ct_fat_measure_aggregate_split_reports(csv_reports)
#
#     if filepath_only:
#         # TODO write to file
#         pass
# 
#     return agg_report

def __ct_fat_measure_aggregate_split_reports(csv_reports):
    print(csv_reports[0])
    return None

def __ct_fat_measure_move_files(dcm_files_directory, interval, split_dir):

    dcm_files = sorted(os.listdir(dcm_files_directory))
    start, end = interval

    for i in range(start, end):
        dcm_file = dcm_files[i]
        dcm_filename = os.path.split(dcm_file)[1]
        copyfile(os.path.join(dcm_files_directory, dcm_file), os.path.join(split_dir, dcm_filename))


def __ct_fat_measure(source_file, request_name, filepath_only):
    payload = {"source_file": source_file}
    worker_hostname = os.environ["CT_FAT_MEASURE_HOSTNAME"]
    worker_port     = os.environ["CT_FAT_MEASURE_PORT"]

    cr = ContainerRequester()
    response_dict = cr.send_request_to_worker(payload, worker_hostname, worker_port, request_name)

    report_path = response_dict["fat_report"]
    print("Report path")

    if filepath_only:
        return report_path

    report_csv = __read_csv_file(report_path)
    __delete_file(report_path)

    return report_csv


def __read_csv_file(filepath):

    with open(filepath) as csv_file:

        lines = csv_file.readlines()
        # remove all whitespaces
        lines = [line.replace(' ', '') for line in lines]

        csv_dict = csv.DictReader(lines)
        dict_rows = []
        for row in csv_dict:
            dict_rows.append(row)

        return dict_rows

# TODO error handling?
def __delete_file(filepath):

    rm_cmd = "rm -rf {}".format(filepath)
    print("Removing {}".format(filepath))
    sb.call([rm_cmd], shell=True)


# for nifti files source is of type: /path/to/file.nii.gz
def ct_muscle_segment_nifti(source_file, filepath_only=False):

    assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

    return __ct_muscle_segment_nifti(source_file, filepath_only=filepath_only)


# for dcm files source is of type: /path/to/directory
def ct_muscle_segment_dcm(source_directory, filepath_only=False):
    assert os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE"

    nifti_filename = __converter_convert_dcm_to_nifti(source_directory)
    return __ct_muscle_segment_nifti(nifti_filename, filepath_only=filepath_only)



def __converter_convert_dcm_to_nifti(source_directory):

    payload         = {'source_dir': source_directory}
    worker_hostname = os.environ["LUNGMASK_CONVERTER_HOSTNAME"]
    worker_port     = os.environ["LUNGMASK_CONVERTER_PORT"]
    request_name    = 'lungmask_convert_dcm_to_nifti'

    cr = ContainerRequester()
    response_dict = cr.send_request_to_worker(payload, worker_hostname, worker_port, request_name)

    relative_nifti_filename = response_dict["filename"]
    data_share              = os.environ["DATA_SHARE_PATH"]

    return relative_nifti_filename


def __ct_muscle_segment_nifti(source_file, filepath_only=False):
    assert __is_nifti(source_file)

    payload         = {'source_file': source_file}
    worker_hostname = os.environ["CT_MUSCLE_SEG_HOSTNAME"]
    worker_port     = os.environ["CT_MUSCLE_SEG_PORT"]
    request_name    = "ct_segment_muscle"

    print("filepath only ", filepath_only)

    cr = ContainerRequester()
    response_dict = cr.send_request_to_worker(payload, worker_hostname, worker_port, request_name)

    rel_seg_path = response_dict["segmentation"]
    data_share = os.environ["DATA_SHARE_PATH"]

    segmentation_path = os.path.join(data_share, rel_seg_path)

    if filepath_only:
        return segmentation_path

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

def lungmask_segment(source_dir, model_name='R231CovidWeb', filepath_only=False):

    if os.environ.get("ENVIRONMENT", "").upper() == "DOCKERCOMPOSE":
        return __docker_lungmask_segment(source_dir, model_name=model_name, filepath_only=filepath_only)

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

def __docker_lungmask_segment(source_dir, model_name, filepath_only):

    payload         = {'source_dir': source_dir, 'model_name': model_name}
    worker_hostname = os.environ['LUNGMASK_HOSTNAME']
    worker_port     = os.environ['LUNGMASK_PORT']
    request_name    = 'lungmask_segment'

    cr = ContainerRequester()
    response_dict = cr.send_request_to_worker(payload, worker_hostname, worker_port, request_name)

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
