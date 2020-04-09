import os
from segmenter import *
import subprocess as sb

def segment_positives():
    directory = "/app/source/ct_lung_volumes/Positive/"

    for i in range(1, 10):
        str_i = "0" + str(i) if i < 10 else str(i)
        case_dir = "Case_0" + str_i

        filename = os.path.join(directory, case_dir)
        print(filename)
        seg_filename = ct_muscle_segment_dcm(filename, filepath_only=True)
        seg_root, seg_name = os.path.split(seg_filename)

        mv_cmd = "mv {} /app/source/output/{}".format(seg_filename, case_dir + seg_name)
        sb.call([mv_cmd], shell=True)

if __name__ == "__main__":
    segment_positives()