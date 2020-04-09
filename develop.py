import os
from segmenter import *
import subprocess as sb
from threading import Thread

def segment_positives():
    directory = "/app/source/ct_lung_volumes/Positive/"

    for i in range(1, 11):
        str_i = "0" + str(i) if i < 10 else str(i)
        case_dir = "Case_0" + str_i

        filename = os.path.join(directory, case_dir)
        print(filename)
        seg_filename = ct_muscle_segment_dcm(filename, filepath_only=True)
        seg_root, seg_name = os.path.split(seg_filename)

        mv_cmd = "mv {} /app/source/output/{}".format(seg_filename, case_dir + "muscle_seg.nii.gz")
        sb.call([mv_cmd], shell=True)

def segment_negatives():


    directory = "/app/source/ct_lung_volumes/Negative2"
    dirs = ["BE001", "BE002", "BE006", "BE007", "BE010", "LC001", "LC002", "LC003", "LC008", "LC009"]

    for case_dir in dirs:

        filename = os.path.join(directory, case_dir)
        print(filename)
        seg_filename = ct_muscle_segment_dcm(filename, filepath_only=True)

        mv_cmd = "mv {} /app/source/output/{}".format(seg_filename, case_dir + "_muscle_seg.nii.gz")
        sb.call([mv_cmd], shell=True)


def get_fat_measurements_positive():

    directory = "/app/source/ct_lung_volumes/Positive/"
    threads = []

    for i in range(1, 11):
        str_i = "0" + str(i) if i < 10 else str(i)
        case_dir = "Case_0" + str_i

        thread = Thread(target=lambda: __start_measurement(directory, case_dir, "_pos_fat_report.txt"))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()



def __start_measurement(directory, case_dir, suffix):
    filename = os.path.join(directory, case_dir)
    print(filename)
    seg_filename = ct_fat_measure_dcm(filename, filepath_only=True)

    mv_cmd = "mv {} /app/source/output/{}".format(seg_filename, case_dir + suffix)
    sb.call([mv_cmd], shell=True)

def get_fat_measurements_negative():

    directory = "/app/source/ct_lung_volumes/Negative2"
    dirs = ["BE001", "BE002", "BE006", "BE007", "BE010", "LC001", "LC002", "LC003", "LC008", "LC009"]
    threads = []

    for case_dir in dirs:

        thread = Thread(target=lambda: __start_measurement(directory, case_dir, "_neg_fat_report.txt"))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    get_fat_measurements_positive()
