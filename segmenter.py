from workers.ct_fat_measure import CTFatMeasurer
from workers.ct_muscle_segment import CTMuscleSegmenter
from workers.lungmask_segment import LungmaskSegmenter
from workers.covid_detector import CovidDetector
from workers.covid_detector_seg import CovidDetectorSeg
from container_requester import ContainerRequester
import os

# ALL PATHS INPUTTED ARE RELATIVE TO $DATA_SHARE_PATH

def covid_detector_nifti(source_file, filepath_only=False):

    cr = ContainerRequester()
    covid_detector = CovidDetector(cr)

    return covid_detector.generate_detection_and_attention_maps_nifti(source_file, filepath_only=filepath_only)

def covid_detector_dcm(source_file, filepath_only=False):

    cr = ContainerRequester()
    covid_detector = CovidDetector(cr)

    return covid_detector.generate_detection_and_attention_maps_dcm(source_file, filepath_only=filepath_only)

def covid_detector_seg_nifti(source_file, filepath_only=False):

    cr = ContainerRequester()
    covid_detector = CovidDetectorSeg(cr)

    return covid_detector.generate_detection_and_attention_maps_nifti(source_file, filepath_only=filepath_only)

def covid_detector_seg_dcm(source_file, filepath_only=False):

    cr = ContainerRequester()
    covid_detector = CovidDetectorSeg(cr)

    return covid_detector.generate_detection_and_attention_maps_dcm(source_file, filepath_only=filepath_only)

def ct_fat_measure_nifti(source_file, filepath_only=False):

    cr = ContainerRequester()
    ct_fat_measurer = CTFatMeasurer(cr)

    return ct_fat_measurer.measure_nifti(source_file, filepath_only=filepath_only)


def ct_fat_measure_dcm(source_file, filepath_only=False, split=False):

    cr = ContainerRequester()
    ct_fat_measurer = CTFatMeasurer(cr)

    return ct_fat_measurer.measure_dcm(source_file, filepath_only=filepath_only)



# for nifti files source is of type: /path/to/file.nii.gz
def ct_muscle_segment_nifti(source_file, filepath_only=False):

    cr = ContainerRequester()
    ct_muscle_seg = CTMuscleSegmenter(cr)

    return ct_muscle_seg.segment_nifti(source_file, filepath_only=filepath_only)


# for dcm files source is of type: /path/to/directory
def ct_muscle_segment_dcm(source_directory, filepath_only=False):

    cr = ContainerRequester()
    ct_muscle_seg = CTMuscleSegmenter(cr)

    return ct_muscle_seg.segment_dcm(source_directory, filepath_only=filepath_only)


def lungmask_segment(source_dir, model_name='R231CovidWeb', filepath_only=False):

    cr = ContainerRequester()
    lungmask_seg  = LungmaskSegmenter(cr)

    return lungmask_seg.segment(source_dir, model_name=model_name, filepath_only=filepath_only)




def is_nifti(filepath):

    file = os.path.split(filepath)[1]

    file_exts = file.split('.')
    if len(file_exts) < 3:
        return False

    nii = file_exts[len(file_exts) - 2]
    gz  = file_exts[-1]

    return nii == "nii" and gz == "gz"
