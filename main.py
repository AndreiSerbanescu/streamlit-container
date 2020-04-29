import streamlit as st
import numpy as np
from PIL import Image
import sys
import xnat
import os
import SimpleITK as sitk
import segmenter
from pathlib import Path
from matplotlib import pyplot as plt
from plotter import generateHUplots
import subprocess as sb
from functools import reduce
import operator
from workers.nifti_reader import read_nifti_image
from concurrent.futures import ThreadPoolExecutor

LUNGMASK_SEGMENT = "Lungmask Segmentation"
CT_FAT_REPORT = "CT Fat Report"
CT_MUSCLE_SEGMENTATION = "CT Muscle Segmentation"
LESION_DETECTION = "Lesion Detection"
LESION_DETECTION_SEG = "Lesion Detection Segmentation"

def analyze(img, msk, num_thresholds = 100):

    X = img[msk].flatten()
    X = X[X>-1024]
    num_pts = len(X.flatten())

    min_hu = -1024
    max_hu = 500
    step = (max_hu - min_hu) / num_thresholds
    thresholds = list(np.arange(min_hu+step, max_hu+step, step))
    counts = [len(X[X < t].flatten()) / num_pts for t in thresholds] 
    
    return counts, thresholds


def get_files(connection, project, subject, session, scan, resource):
    xnat_project = project#connection.projects[project]
    xnat_subject = subject#xnat_project.subjects[subject]
    xnat_experiment = session#xnat_subject.experiments[session]
    xnat_scan = scan#xnat_experiment.scans[scan]
    files = resource.files.values()
    return files

def get_worker_information():

    worker_names = [LUNGMASK_SEGMENT, CT_FAT_REPORT, CT_MUSCLE_SEGMENTATION,
                    LESION_DETECTION, LESION_DETECTION_SEG]

    worker_methods = {
        LUNGMASK_SEGMENT: lungmask_segment,
        CT_FAT_REPORT: ct_fat_report,
        CT_MUSCLE_SEGMENTATION: ct_muscle_segment,
        LESION_DETECTION: lesion_detect,
        LESION_DETECTION_SEG: lesion_detect_seg
    }

    return worker_methods, worker_names

def ct_fat_report(source_file):
    print("ct fat report called with", source_file)

    if segmenter.is_nifti(source_file):
        return segmenter.ct_fat_measure_nifti(source_file)
    else:
        return segmenter.ct_fat_measure_dcm(source_file)

def convert_report_to_cm3(fat_report):

    last_row = fat_report[-1]
    fat_report = fat_report[:len(fat_report) - 1]

    visceral_tissue = 0
    subcutaneous_tissue = 0
    for row in fat_report:
        visceral_tissue += float(row['vatVol'])
        subcutaneous_tissue += float(row['satVol'])

    total_in_cm3 = float(last_row["tatVol"])
    total = visceral_tissue + subcutaneous_tissue

    ratio = total_in_cm3 / total

    fat_report_cm3 = []
    for row in fat_report:
        visceral_tissue = float(row['vatVol'])
        subcutaneous_tissue = float(row['satVol'])

        visc_tissue_cm3 = ratio * visceral_tissue
        subcut_tissue_cm3 = ratio * subcutaneous_tissue

        row_dict_cm3 = {
            'vatVol': visc_tissue_cm3,
            'satVol': subcut_tissue_cm3
        }

        fat_report_cm3.append(row_dict_cm3)

    return fat_report_cm3

def display_fat_report(fat_report):

    # if fat_report is None:
    #     return

    paper_citation = "**Fat Measurement by:** Summers RM, Liu J, Sussman DL, Dwyer AJ, Rehani B, Pickhardt PJ, Choi JR, Yao J. Association " \
                     "Between Visceral Adiposity and Colorectal Polyps on CT Colonography. AJR 199:48–57 (2012)."\
                     "Ryckman EM, Summers RM, Liu J, Del Rio AM, Pickhardt PJ. Visceral fat quantification in asymptomatic " \
                     "adults using abdominal CT: is it predictive of future cardiac events? Abdom Imaging 40:222–225 (2015)."\
                     "Liu J, Pattanaik S, Yao J, Dwyer AJ, Pickhardt PJ, Choi JR, Summers RM. Associations among Pericolonic Fat, Visceral Fat, " \
                     "and Colorectal Polyps on CT Colonography. Obesity 23:470-476 (2015)."\
                     "Lee SJ, Liu J, Yao J, Kanarek A, Summers RM, Pickhardt PJ. Fully Automated Segmentation" \
                     " and Quantification of Visceral and Subcutaneous Fat at Abdominal CT: Application to a " \
                     "longitudinal adult screening cohort. Br J Radiol 91(1089):20170968 (2018)"

    st.markdown(paper_citation)
    st.markdown('**Fat Report**')

    sat_vols = [elem['satVol'] for elem in fat_report]
    vat_vols = [elem['vatVol'] for elem in fat_report]

    st.markdown("**Total fat tissue information**")
    __display_agg_fat_report_info(sat_vols, vat_vols, 0, len(sat_vols))

    st.markdown("**Lower half tissue information**")
    __display_agg_fat_report_info(sat_vols, vat_vols, len(sat_vols) // 2, len(sat_vols))

    st.markdown("**Lower third tissue information**")
    __display_agg_fat_report_info(sat_vols, vat_vols, len(sat_vols) * 2 // 3, len(sat_vols))

    from_slice = 100
    to_slice = 230

    st.markdown(f"**Custom from slice {from_slice} to slice {to_slice}**")
    __display_agg_fat_report_info(sat_vols, vat_vols, from_slice, to_slice)

def __display_agg_fat_report_info(sat_vols, vat_vols, from_slice, to_slice):
    # from_slice inclusive
    # to_slice exclusive

    partial_sats = sat_vols[from_slice:to_slice]
    partial_vats = vat_vols[from_slice:to_slice]

    sat_tissue_cm3 = reduce(operator.add, partial_sats)
    vat_tissue_cm3 = reduce(operator.add, partial_vats)

    st.text(f"visceral to subcutaneous ratio {vat_tissue_cm3 / sat_tissue_cm3}")
    st.text(f"visceral volume: {vat_tissue_cm3:.2f} cm3")
    st.text(f"subcutaneous volume: {sat_tissue_cm3:.2f} cm3")


def __display_partial_volume(volume, from_slice, to_slice):

    volume_array = sitk.GetArrayFromImage(volume)

    cm = plt.get_cmap('gray')
    cm_hot = plt.get_cmap('inferno')  # copper
    zd, yd, xd = volume_array.shape

    im = volume_array[from_slice:to_slice, yd // 2, :]
    im = np.uint8(cm(im) * 255)

    im = Image.fromarray(im).convert('RGB')
    im = im.resize((150, 150))
    # im = np.uint8(cm_hot(segmentation_array[i, :, :].astype(float) / num_labels) * 255)
    # im = Image.fromarray(im).convert('RGB')
    # imgs.append(im.resize((150, 150)))
    st.image(im)

# TODO here we assume (from observation)
# the last row shows the true volume in cm cubed
def __display_fat_report(report, last_row):
    visceral_tissue = 0
    subcutaneous_tissue = 0
    sanity_check_total = 0
    for row in report:
        visceral_tissue += float(row['vatVol'])
        subcutaneous_tissue += float(row['satVol'])
        sanity_check_total += float(row['tatVol'])

    total_in_cm3 = float(last_row["tatVol"])

    visceral_tissue, subcutaneous_tissue = transform_in_cm3(visceral_tissue, subcutaneous_tissue, total_in_cm3)
    total_tissue = visceral_tissue + subcutaneous_tissue
    visceral_ratio = visceral_tissue / total_tissue
    subcut_ratio = subcutaneous_tissue / total_tissue
    visc_to_subcut_ratio = visceral_tissue / subcutaneous_tissue

    st.text(f"visceral to subcutaneous ratio {visc_to_subcut_ratio}")
    st.text(f"visceral ratio {visceral_ratio}")
    st.text(f"subcutaneous ratio {subcut_ratio}")

def transform_in_cm3(visceral_tissue, subcutaneous_tissue, total_in_cm3):
    total = visceral_tissue + subcutaneous_tissue

    ratio = total_in_cm3 / total

    visceral_in_cm3 = ratio * visceral_tissue
    subcutaneous_in_cm3 = ratio * subcutaneous_tissue
    return visceral_in_cm3, subcutaneous_in_cm3

def ct_muscle_segment(source_file):
    print("ct muscle segment called with", source_file)

    if segmenter.is_nifti(source_file):
        muscle_segmentation, original = segmenter.ct_muscle_segment_nifti(source_file)
    else:
        muscle_segmentation, original = segmenter.ct_muscle_segment_dcm(source_file)

    return muscle_segmentation


# PRE: original array and lung segmentation not None
# rest can be None
def display_volume_and_slice_information(original_array, lung_seg, muscle_seg=None, detection_array=None,
                                         attention_array=None, fat_report_cm3=None):

    assert original_array is not None
    assert lung_seg is not None

    display_lungmask_segmentation(original_array, lung_seg)

    if fat_report_cm3 is not None:
        display_fat_report(fat_report_cm3)

    __display_information_rows(original_array, lung_seg, muscle_seg, detection_array, attention_array, fat_report_cm3)

def display_lungmask_segmentation(original_array, segmentation_array):

    input_nifti = sitk.GetImageFromArray(original_array)
    spx, spy, spz = input_nifti.GetSpacing()

    st.header("HU distribution:")
    generateHUplots.generateHUPlots(original_array, segmentation_array, 2)

    right = np.count_nonzero(segmentation_array == 1) * spx * spy * spz
    left = np.count_nonzero(segmentation_array == 2) * spx * spy * spz

    st.header("Result:")
    st.header(f'right lung: {right} mm\N{SUPERSCRIPT THREE}')
    st.header(f'left lung: {left} mm\N{SUPERSCRIPT THREE}')

    st.markdown('**Lung Segmentation by:** Johannes Hofmanninger, Forian Prayer, Jeanny Pan, Sebastian Röhrich, \
                        Helmut Prosch and Georg Langs. "Automatic lung segmentation in routine imaging \
                        is a data diversity problem, not a methodology problem". 1 2020, \
                        [https://arxiv.org/abs/2001.11767](https://arxiv.org/abs/2001.11767)')


def __display_information_rows(original_array, lung_seg, muscle_seg, detection_array, attention_array, fat_report_cm3):


    if muscle_seg is not None:
        muscle_citation = "**Muscle Segmentation by:** Burns JE, Yao J, Chalhoub D, Chen JJ, Summers RM. A Machine Learning Algorithm to Estimate Sarcopenia on Abdominal CT. Academic Radiology 27:311–320 (2020)."\
                          "Graffy P, Liu J, Pickhardt PJ, Burns JE, Yao J, Summers RM. Deep Learning-Based Muscle Segmentation and Quantification at Abdominal CT: Application to a longitudinal adult screening cohort for sarcopenia assessment. Br J Radiol 92:20190327 (2019)."\
                          "Sandfort V, Yan K, Pickhardt PJ, Summers RM. Data augmentation using generative adversarial networks (CycleGAN) to improve generalizability in CT segmentation tasks. Scientific Reports (2019) 9:16884."

        st.markdown(muscle_citation)

    original_imgs = get_slices_from_volume(original_array, lung_seg)
    lung_seg_imgs = get_mask_slices_from_volume(lung_seg)

    tuple_imgs = [original_imgs, lung_seg_imgs]
    captions = ["Volume", "Lung Mask"]

    if muscle_seg is not None:
        muscle_seg_imgs = get_mask_slices_from_volume(muscle_seg)
        tuple_imgs.append(muscle_seg_imgs)
        captions.append("Muscle Mask")

    if detection_array is not None:
        detection_imgs = get_slices_from_volume(detection_array, lung_seg)
        tuple_imgs.append(detection_imgs)
        captions.append("Detection Boxes")

    if attention_array is not None:
        attention_imgs = get_slices_from_volume(attention_array, lung_seg)
        tuple_imgs.append(attention_imgs)
        captions.append("Attention")

    tuple_imgs = tuple(tuple_imgs)

    all_imgs = list(zip(*tuple_imgs))

    for idx in range(len(all_imgs)):

        st.text(f"Slice {idx + 1} / {len(all_imgs)}")

        if fat_report_cm3 is not None:
            vatVol_cm3 = fat_report_cm3[idx]['vatVol']
            satVol_cm3 = fat_report_cm3[idx]['satVol']

            st.text(f"Visceral volume {vatVol_cm3:.3f} cm3")
            st.text(f"Subcutaneous volume {satVol_cm3:.3f} cm3")


        img_tuple = all_imgs[idx]

        img_list = list(img_tuple)
        st.image(img_list, caption=captions)



def get_slices_from_volume(original_array, lung_seg):
    imgs = []
    cm = plt.get_cmap('gray')
    zd = original_array.shape[0]

    for i in range(zd):
        mskmax = original_array[lung_seg > 0].max()
        mskmin = original_array[lung_seg > 0].min()
        im_arr = (original_array[i, :, :].astype(float) - mskmin) * (1.0 / (mskmax - mskmin))
        im_arr = np.uint8(cm(im_arr) * 255)
        im = Image.fromarray(im_arr).convert('RGB')
        imgs.append(im.resize((250, 250)))

    return imgs

def get_mask_slices_from_volume(mask_array):
    num_labels = mask_array.max()
    imgs = []
    cm_hot = plt.get_cmap('inferno')  # copper
    zd = mask_array.shape[0]
    for i in range(zd):
        mask_cm_hot = np.uint8(cm_hot(mask_array[i, :, :].astype(float) / num_labels) * 255)
        mask = Image.fromarray(mask_cm_hot).convert('RGB')
        imgs.append(mask.resize((250, 250)))

    return imgs

def lesion_detect(source_file):
    print("lesion detect called with", source_file)

    if segmenter.is_nifti(source_file):
        attention_volume, detection_volume = segmenter.covid_detector_nifti(source_file)
    else:
        attention_volume, detection_volume = segmenter.covid_detector_dcm(source_file)


    return attention_volume, detection_volume


def lesion_detect_seg(source_file):
    print("lesion detect seg called with", source_file)

    if segmenter.is_nifti(source_file):
        mask_volume, detection_volume = segmenter.covid_detector_seg_nifti(source_file)
    else:
        mask_volume, detection_volume = segmenter.covid_detector_seg_dcm(source_file)

    return mask_volume, detection_volume


def lungmask_segment(source_dir):
    segmentation, input_nda, spx, spy, spz = segmenter.lungmask_segment(source_dir, model_name='R231CovidWeb')
    return segmentation, input_nda

def move_files_to_shared_directory(source_dir):

    data_share = os.environ["DATA_SHARE_PATH"]
    input = "streamlit_input"
    abs_input_path = os.path.join(data_share, input)

    if not os.path.exists(abs_input_path):
        os.mkdir(abs_input_path)

    cp_cmd = "cp -r {} {}".format(source_dir, abs_input_path)
    exit_code = sb.call([cp_cmd], shell=True)

    if exit_code == 1:
        raise Exception("Couldn't move input files from {} to {}".format(source_dir, abs_input_path))

    # TODO fix hardcoding
    return os.path.join(input, "files")

# TODO delete this
def read_csv(filepath):

    import csv
    with open(filepath) as csv_file:
        lines = csv_file.readlines()
        # remove all whitespaces
        lines = [line.replace(' ', '') for line in lines]

        csv_dict = csv.DictReader(lines)
        dict_rows = []
        for row in csv_dict:
            dict_rows.append(row)

        return dict_rows

def start_download_and_analyse(source_dir, workers_selected):

    if len(workers_selected) == 0:
        st.markdown("**Need to select at least one container**")
        return

    worker_methods = get_worker_information()[0]

    future_map = {}
    with ThreadPoolExecutor() as executor:

        for worker in workers_selected:
            method = worker_methods[worker]

            future = executor.submit(method, source_dir)
            future_map[worker] = future

    value_map = {}
    for key in future_map:
        future = future_map[key]

        value = future.result()
        value_map[key] = value

    # TODO refactor
    LUNGMASK_SEGMENT = "Lungmask Segmentation"
    CT_FAT_REPORT = "CT Fat Report"
    CT_MUSCLE_SEGMENTATION = "CT Muscle Segmentation"
    LESION_DETECTION = "Lesion Detection"
    LESION_DETECTION_SEG = "Lesion Detection Segmentation"


    # TODO here source dir assumes its nifti
    # here source_dir assume
    # TODO fix hardcoding

    # TODO make sure source dir is not empty

    muscle_mask = value_map.get(CT_MUSCLE_SEGMENTATION, None)
    detection_volume = value_map.get(LESION_DETECTION, (None, None))[1]
    lungmask_array, volume_array = value_map.get(LUNGMASK_SEGMENT, (None, None))
    fat_report = value_map.get(CT_FAT_REPORT, None)

    muscle_mask_array = sitk.GetArrayFromImage(muscle_mask) if muscle_mask is not None else None
    detection_volume_array = sitk.GetArrayFromImage(detection_volume) if detection_volume is not None else None

    fat_report_cm3 = convert_report_to_cm3(fat_report) if fat_report is not None else None

    display_volume_and_slice_information(volume_array, lungmask_array, muscle_mask_array,
                                         detection_volume_array, fat_report_cm3)

def download_and_analyse_button_xnat(subject_name, scan, workers_selected):
    if st.button('download and analyse'):
        latest_iteration = st.empty()

        bar = st.progress(0)

        dir_ = os.path.join('/tmp/', subject_name)
        scan.download_dir(dir_, verbose=True)
        download_dir = ''
        for path in Path(dir_).rglob('*.dcm'):
            download_dir, file = os.path.split(str(path.resolve()))
            break
        bar.progress(100)

        st.text('Analysis progress...')

        source_dir = move_files_to_shared_directory(download_dir)
        start_download_and_analyse(source_dir, workers_selected)

    debug_display_button()



def download_and_analyse_button_upload(uploaded_file, workers_selected):

    if st.button('download and analyse'):
        print(uploaded_file)
        # writing file to disk
        # this is docker specific
        # TODO allow for .nii as well

        file_type = ".nii.gz"
        filename = os.path.join(os.environ['DATA_SHARE_PATH'], "input" + file_type)

        with open(filename, "wb") as f:
            try:
                f.write(uploaded_file.getbuffer())
            except:
                st.markdown("**No file uploaded**")
                return

        source_dir = os.path.split(filename)[1]

        start_download_and_analyse(source_dir, workers_selected)

    debug_display_button()

def debug_display_button():

    if os.environ.get('DEBUG', '') == '1' and st.button('Show Worker Display'):
        # TODO refactor
        LUNGMASK_SEGMENT = "Lungmask Segmentation"
        CT_FAT_REPORT = "CT Fat Report"
        CT_MUSCLE_SEGMENTATION = "CT Muscle Segmentation"
        LESION_DETECTION = "Lesion Detection"
        LESION_DETECTION_SEG = "Lesion Detection Segmentation"

        volume = sitk.ReadImage('/app/source/all_outputs/input.nii.gz')
        volume_array = sitk.GetArrayFromImage(volume)

        lungmask_array = np.load('source/all_outputs/lungmask_for_streamlit-segmentation-1588003852.7941797.npy')

        fat_report_cm3 = None
        muscle_array = None
        lesion_detect_array = None
        lesion_attention_array = None

        if CT_FAT_REPORT in workers_selected:
            fat_report = read_csv('/app/source/all_outputs/fat_report_converted_case001.txt')
            fat_report_cm3 = convert_report_to_cm3(fat_report)

        if CT_MUSCLE_SEGMENTATION in workers_selected:
            muscle_seg = sitk.ReadImage('/app/source/all_outputs/muscle_segment_converted_case001.nii.gz')
            muscle_array = sitk.GetArrayFromImage(muscle_seg)

        if LESION_DETECTION in workers_selected:
            lesion_detect = sitk.ReadImage('/app/source/all_outputs/detection_converted-case001.nii.gz')
            lesion_detect_array = sitk.GetArrayFromImage(lesion_detect)

        if LESION_DETECTION_SEG in workers_selected:
            lesion_attention = sitk.ReadImage('/app/source/all_outputs/attention_converted-case001.nii.gz')
            lesion_attention_array = sitk.GetArrayFromImage(lesion_attention)

        display_volume_and_slice_information(volume_array, lungmask_array, muscle_array, lesion_detect_array,
                                             lesion_attention_array, fat_report_cm3)

def worker_selection():
    # TODO removing hardcoing of available containers
    # TODO have better names
    worker_methods, worker_names = get_worker_information()

    worker_names.remove(LUNGMASK_SEGMENT)

    st.text("Running lungmask segmentation by default")
    workers_selected = st.multiselect('Containers', worker_names)

    # lungmask segment runs by default
    workers_selected.append(LUNGMASK_SEGMENT)
    return workers_selected

if __name__ == "__main__":
    print(sys.version)
    #lung = Image.open("lung.png").resize((500, 500))
    #seg = Image.open("seg.png").resize((500, 500))

    #### Page Header #####
    # st.title("CoCaCoLA - The Cool Calculator for Corona Lung Assessment")
    st.title("CoViD-19 Risk Calculator")  # for more formal occasions :S
    pcr_positive = st.checkbox("PCR Positive?")
    #### Page Header #####

    ##### Sidebar ######
    st.sidebar.title("Clinical Data")
    st.sidebar.subheader("Basic Data")
    sex = st.sidebar.selectbox("Sex", ("Male", "Female"))
    age = st.sidebar.number_input("Age", min_value=0, max_value=110, step=1, value=50)
    weight = st.sidebar.number_input("Weight", min_value=0, max_value=150, step=1, value=70)
    height = st.sidebar.number_input(
        "Height", min_value=120, max_value=200, step=1, value=160
    )
    st.sidebar.subheader("Pre-existing Conditions")
    diabetes = st.sidebar.checkbox("Diabetes")
    smoking = st.sidebar.checkbox("Smoking")
    emphysema = st.sidebar.checkbox("Pulmonary Disease")
    stroke = st.sidebar.checkbox("Previous Stroke")
    cardiac = st.sidebar.checkbox("Cardiac Disease")
    oncologic = st.sidebar.checkbox("Cancer")
    immuno = st.sidebar.checkbox("Immunodeficiency or Immunosuppression")

    st.sidebar.subheader("Laboratory")
    lymphos = st.sidebar.selectbox("Lymphocytes", ("Lowered", "Normal", "Elevated"))
    crp = st.sidebar.number_input("CRP", min_value=0.0, max_value=50.0, step=0.1, value=0.5)
    crea = st.sidebar.number_input(
        "Creatinine", min_value=0.0, max_value=5.0, step=0.1, value=1.0
    )
    dimers = st.sidebar.number_input(
        "D-Dimers", min_value=0, max_value=5000, step=100, value=500
    )
    ldh = st.sidebar.number_input("LDH", min_value=0, max_value=5000, step=10, value=240)
    ##### Sidebar ######

    ##### XNAT connection #####
    #this is behind a VPN so you need to connect your own XNAT


    if st.checkbox("Toggle between xnat server and upload"):
        files_from_xnat_server = True

        xnat_working = True
        xnat_address = 'http://armada.doc.ic.ac.uk/xnat-web-1.7.6'
        xnat_user = "admin"
        xnat_password = "admin"

        try:
            with xnat.connect(xnat_address, user=xnat_user, password=xnat_password) as session:

                pn = [x.name for x in session.projects.values()]
                project_name = st.selectbox('Project', pn)
                project = session.projects[project_name]

                sn = [x.label for x in project.subjects.values()]
                subject_name = st.selectbox('Subject', sn)
                subject = project.subjects[subject_name]

                en = [x.label for x in subject.experiments.values()]
                experiment_name = st.selectbox('Session', en)
                experiment = subject.experiments[experiment_name]

                sen = [x.type for x in experiment.scans.values()]
                scan_name = st.selectbox('Scan', sen)
                scan = experiment.scans[scan_name]

                sen = [x.label for x in scan.resources.values()]
                res_name = st.selectbox('Resources', sen)
                resource = scan.resources[res_name]

                workers_selected = worker_selection()
                download_and_analyse_button_xnat(subject_name, scan, workers_selected)

        except Exception as e:
            xnat_working = False
            st.text(f"xnat server {xnat_address} not working")
            print("xnat exception", e)

    else:

        files_from_xnat_server = False
        ##### File Selector #####
        # TODO upload of several (DICOM) files needs the streamlit dev version, which is difficult to use
        st.header("Please Upload the Chest CT Nifti here")
        # uploaded_file = st.file_uploader(label="", type=["nii", "nii.gz"])
        # TODO allow nii as well
        uploaded_file = st.file_uploader(label="", type=["nii.gz"])

        workers_selected = worker_selection()
        download_and_analyse_button_upload(uploaded_file, workers_selected)

        ##### File Selector #####


    ##### XNAT connection #####

    ##### Output Area #####
    #st.header("Result:")
    #st.subheader("Probability of Covid-19 infection=96.5%")
    #st.subheader("Covid-19 severity index: 1")

    ##### Output Area #####
    #st.image([lung, seg])

