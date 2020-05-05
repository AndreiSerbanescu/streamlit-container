import os
from segmenter import lungmask_segment
import shutil
from exceptions.workers import WorkerFailedException
from testing.segmentation_metrics import get_complete_set_of_dice_scores, get_complete_set_of_iou_scores
from workers.nifti_reader import read_nifti_image
import json
from threading import Thread

def generate_lungmask_segmentations_with_ground_files():
    testing_dir = os.environ["NIFTI_TESTING_DIR"]
    testing_out_dir = os.environ["TESTING_OUT_DIR"]

    os.makedirs(testing_out_dir, exist_ok=True)

    # copy all files from the testing directory
    # somewhere in the data share directory

    # how is the input image named e.g. "image.nii.gz" or "input.nii.gz"
    input_name = os.environ["NIFTI_TESTING_INPUT_NAME"]

    data_share = os.environ["DATA_SHARE_PATH"]
    testing_dir_name = os.path.split(testing_dir)[1]

    data_share_testing_dir = os.path.join(data_share, testing_dir_name)

    shutil.copytree(testing_dir, data_share_testing_dir)

    # walk testing data in data share directory and send
    # requests to lungmask

    subfolders = [f.path for f in os.scandir(data_share_testing_dir) if f.is_dir()]

    for subfolder in subfolders:

        subject_file = os.path.join(subfolder, input_name)
        print(f"## subject file {subject_file}")

        rel_subject_file = os.path.relpath(subject_file, data_share)
        print(f"## rel subject file {rel_subject_file}")

        subject_name = os.path.split(subfolder)[1]

        subject_testing_output = os.path.join(testing_out_dir, subject_name)
        print(f"## subject testing output {subject_testing_output}")

        if os.path.exists(subject_testing_output):
            print(f"## subject testing output {subject_testing_output} exists already")

        os.makedirs(subject_testing_output, exist_ok=True)

        subject_shared_output_dir = os.path.join(subject_testing_output, "lungmask_nifti.nii.gz")
       
        shutil.copyfile(os.path.join(subfolder, "mask_Lung_L.nii.gz"),
                        os.path.join(subject_testing_output, "ground_left.nii.gz"))

        shutil.copyfile(os.path.join(subfolder, "mask_Lung_R.nii.gz"),
                        os.path.join(subject_testing_output, "ground_right.nii.gz"))

        shutil.copyfile(subject_file, os.path.join(subject_testing_output, "input.nii.gz"))
        
        if os.path.exists(subject_shared_output_dir):
            print(f"### {subject_name} aleady computed - skipping")
            continue

        try:
            rel_seg_path, rel_input_path = lungmask_segment(rel_subject_file, filepath_only=True)
            full_seg_path = os.path.join(data_share, rel_seg_path)

            shutil.copyfile(full_seg_path, subject_shared_output_dir)
        except WorkerFailedException as e:
            print(f"### EXCEPTION lungmask failed for {subject_name}")

def generate_dicom_segmentations():
    testing_dir = os.environ["DCM_TESTING_DIR"]
    testing_out_dir = os.environ["TESTING_OUT_DIR"]

    os.makedirs(testing_out_dir, exist_ok=True)

    # copy all files from the testing directory
    # somewhere in the data share directory

    data_share = os.environ["DATA_SHARE_PATH"]
    testing_dir_name = os.path.split(testing_dir)[1]

    data_share_testing_dir = os.path.join(data_share, testing_dir_name)

    shutil.copytree(testing_dir, data_share_testing_dir)

    # walk testing data in data share directory and send
    # requests to lungmask

    subfolders = [f.path for f in os.scandir(data_share_testing_dir) if f.is_dir()]

    for subfolder in subfolders:

        dcm_sub_dir = __recursively_find_directory_with_dcm_files(subfolder)

        if dcm_sub_dir == "":
            print(f"### ERROR: couldn't perform test for {subfolder} as couldn't find dcm directory")
            continue

        rel_subject_file = os.path.relpath(dcm_sub_dir, data_share)
        print(f"## rel subject file {rel_subject_file}")

        subject_name = os.path.split(subfolder)[1]

        subject_testing_output = os.path.join(testing_out_dir, subject_name)
        print(f"## subject testing output {subject_testing_output}")

        if os.path.exists(subject_testing_output):
            print(f"## subject testing output {subject_testing_output} exists already")

        os.makedirs(subject_testing_output, exist_ok=True)

        try:
            rel_seg_path, rel_input_path = lungmask_segment(rel_subject_file, filepath_only=True)
            full_seg_path = os.path.join(data_share, rel_seg_path)

            shutil.copyfile(full_seg_path, os.path.join(subject_testing_output, "lungmask_dicom.nii.gz"))
        except WorkerFailedException:
            print(f"### EXCEPTION lungmask failed for {subject_name}")

def __recursively_find_directory_with_dcm_files(directory):
    for root, dirs, files in os.walk(directory):
        if len(files) > 1:
            return os.path.join(directory, root)

    return ""

def generate_dice_scores():
    generate_metric_scores(get_complete_set_of_dice_scores, "dice")

def generate_iou_scores():
    generate_metric_scores(get_complete_set_of_iou_scores, "iou")

def generate_metric_scores(metric, metric_name):
    dir = os.environ["TESTING_OUT_DIR"]
    subfolders = sorted([f.path for f in os.scandir(dir) if f.is_dir()])
    for subject in subfolders:
        __get_score_for_subject(metric, metric_name, subject)


def __get_score_for_subject(metric, metric_name, subject):
    metric_score_filename = os.path.join(subject, f"{metric_name}_scores.json")

    subject_name = os.path.split(subject)[1]

    if os.path.exists(metric_score_filename):
        print(f"{metric_name} scores for {subject_name} already exists - skipping")
        return

    print(f"starting {metric_name} computation for {subject_name}")

    ground_left_path = os.path.join(subject, "ground_left.nii.gz")
    ground_right_path = os.path.join(subject, "ground_right.nii.gz")

    nifti_seg_path = os.path.join(subject, "lungmask_nifti.nii.gz")
    dicom_seg_path = os.path.join(subject, "lungmask_dicom.nii.gz")

    ground_left = read_nifti_image(ground_left_path)
    ground_right = read_nifti_image(ground_right_path)

    nifti_seg = read_nifti_image(nifti_seg_path)
    dicom_seg = read_nifti_image(dicom_seg_path)

    try:
        left_nifti_score, right_nifti_score, both_nifti_score = metric(nifti_seg, ground_left, ground_right)
        print(f"{metric_name} finished nifti")
        left_dicom_score, right_dicom_score, both_dicom_score = metric(dicom_seg, ground_left, ground_right)
        print(f"{metric_name} finished dicom")

        mean_nifti_score = (left_nifti_score + right_nifti_score) / 2
        mean_dicom_score = (left_dicom_score + right_dicom_score) / 2

        nifti_dict = {
            "left": left_nifti_score,
            "right": right_nifti_score,
            "mean": mean_nifti_score,
            "full": both_nifti_score
        }

        dicom_dict = {
            "left": left_dicom_score,
            "right": right_dicom_score,
            "mean": mean_dicom_score,
            "full": both_dicom_score
        }

        json_dict = {
            "nifti": nifti_dict,
            "dicom": dicom_dict
        }

        with open(metric_score_filename, "w") as outfile:
            json.dump(json_dict, outfile)

    except Exception as e:
        print(f"### ERRROR: {metric_name} computation failed for {subject_name}")
        print(f"### {metric_name}with exception {e}")

if __name__ == "__main__":
    generate_dice_scores()
    generate_iou_scores()
