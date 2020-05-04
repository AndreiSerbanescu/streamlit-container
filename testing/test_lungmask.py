import os
from segmenter import lungmask_segment
import shutil
from exceptions.workers import WorkerFailedException

def test_nifti():
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

        try:
            rel_seg_path, rel_input_path = lungmask_segment(rel_subject_file, filepath_only=True)
            full_seg_path = os.path.join(data_share, rel_seg_path)

            shutil.copyfile(full_seg_path, os.path.join(subject_testing_output, "lungmask.nii.gz"))
        except WorkerFailedException as e:
            print(f"### EXCEPTION lungmask failed for {subject_name}")

def test_dicom():
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

            shutil.copyfile(full_seg_path, os.path.join(subject_testing_output, "lungmask.nii.gz"))
        except WorkerFailedException:
            print(f"### EXCEPTION lungmask failed for {subject_name}")

def __recursively_find_directory_with_dcm_files(directory):
    for root, dirs, files in os.walk(directory):
        if len(files) > 1:
            return os.path.join(directory, root)

    return ""


if __name__ == "__main__":
    test_dicom()