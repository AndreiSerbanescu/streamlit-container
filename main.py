import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_boston
from PIL import Image

import sys
import xnat
import os
import pydicom
import concurrent.futures
import SimpleITK as sitk
import logging
import segmenter
from pathlib import Path
import dicom2nifti
from pydicom.pixel_data_handlers import gdcm_handler, pillow_handler
from matplotlib import pyplot as plt
#import gdcm #big problem in virutal environments
from plotter import generateHUplots
import subprocess as sb
from threading import Thread
from streamlit.ReportThread import add_report_ctx
from functools import reduce
import operator

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
    LUNGMASK_SEGMENT = "Lungmask Segmentation"
    CT_FAT_REPORT = "CT Fat Report"
    CT_MUSCLE_SEGMENTATION = "CT Muscle Segmentation"
    LESION_DETECTION = "Lesion Detection"
    LESION_DETECTION_SEG = "Lesion Detection Segmentation"

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
        fat_report_csv = segmenter.ct_fat_measure_nifti(source_file)
    else:
        fat_report_csv = segmenter.ct_fat_measure_dcm(source_file)

    data_load_state = st.text('Fat report data')
    # Load 10,000 rows of data into the dataframe.
    # Notify the reader that the data was successfully loaded.
    data_load_state.text('Loading data...done!')

    # TODO better display
    # display_fat_report(fat_report_csv)

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


# def display_fat_report(volume, fat_report):
#
#     st.markdown('**Fat Report - considering lower half**')
#
#     last_row = fat_report[-1]
#     # remove last row
#     fat_report = fat_report[:len(fat_report) - 1]
#     # as of right now displaying information about lower half
#     # half_report = fat_report[len(fat_report) // 2:]
#     # # eliminate final row with aggregate results
#     # sanity_check_last_row = half_report[-1]
#     # half_report = half_report[:len(half_report) - 1]
#
#     from_slice = 100 #TODO select somehow
#     to_slice = 200
#
#     partial_report = fat_report
#     # partial_report = fat_report[from_slice:to_slice]
#
#     __display_fat_report(partial_report, last_row)
#     __display_partial_volume(volume, from_slice, to_slice)
#     print("last row", last_row)

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
    print("visceral", visceral_tissue)
    print("subcut", subcutaneous_tissue)
    print("total", total_tissue)
    print("total sanity check", sanity_check_total)
    print(f"visceral ratio {visceral_ratio}%")
    print(f"sucut ration {subcut_ratio}%")
    print(f"vat to sat {visc_to_subcut_ratio}%")

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

    # TODO here we assume the volume is nifti
    # TODO make ct_muscle_segment return the original volume
    # TODO in nifti format as well

    display_ct_muscle_segment_volume(original, muscle_segmentation)

def display_ct_muscle_segment_volume(original, segmentation):

    segmentation_array = sitk.GetArrayFromImage(segmentation)
    original_array     = sitk.GetArrayFromImage(original)

    spx, spy, spz = original.GetSpacing()

    muscle = np.count_nonzero(segmentation_array == 1) * spx * spy * spz

    st.header("Result:")
    st.header(f'muscle volume: {muscle} mm\N{SUPERSCRIPT THREE}')
    #
    st.markdown('**Muscle Segmentation** by TODO paper here')

    display_volume_and_mask(original_array, segmentation_array)

#
# def display_volume_and_masks(original_array, segmentation_arrays):
#
#     num_labels = [seg.max() for seg in segmentation_arrays]
#     imgs = []
#
#     cm = plt.get_cmap('gray')
#     cm_hot = plt.get_cmap('inferno')
#     zd, yd, xd = original_array.shape
#
#     for i in range(zd):
#

def display_volume_and_slice_information(original_array, lung_seg, muscle_seg, detection_array, fat_report_cm3):

    # assert original_array.shape[0] == lung_seg.shape[0] \
    #         == muscle_seg.shape[0] == len(fat_report_cm3)

    print("len fat report cm 3", len(fat_report_cm3))

    display_lungmask_segmentation(original_array, lung_seg)
    display_fat_report(fat_report_cm3)


    muscle_citation = "**Muscle Segmentation by:** Burns JE, Yao J, Chalhoub D, Chen JJ, Summers RM. A Machine Learning Algorithm to Estimate Sarcopenia on Abdominal CT. Academic Radiology 27:311–320 (2020)."\
                      "Graffy P, Liu J, Pickhardt PJ, Burns JE, Yao J, Summers RM. Deep Learning-Based Muscle Segmentation and Quantification at Abdominal CT: Application to a longitudinal adult screening cohort for sarcopenia assessment. Br J Radiol 92:20190327 (2019)."\
                      "Sandfort V, Yan K, Pickhardt PJ, Summers RM. Data augmentation using generative adversarial networks (CycleGAN) to improve generalizability in CT segmentation tasks. Scientific Reports (2019) 9:16884."

    st.markdown(muscle_citation)
    __display_information_rows(original_array, lung_seg, muscle_seg, detection_array, fat_report_cm3)

def display_lungmask_segmentation(original_array, segmentation_array):

    input_nifti = sitk.GetImageFromArray(original_array)
    spx, spy, spz = input_nifti.GetSpacing()

    # result_out = sitk.GetImageFromArray(segmentation_array)
    # result_out.CopyInformation(input_image)
    # sitk.WriteImage(result_out, os.path.join(dir_, 'segmentation.nii.gz'))
    # bar2.progress(100)

    # output_nda = sitk.GetArrayFromImage(result_out)
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


def __display_information_rows(original_array, lung_seg, muscle_seg, detection_array, fat_report_cm3):
    original_imgs = get_slices_from_volume(original_array, lung_seg)
    lung_seg_imgs = get_mask_slices_from_volume(lung_seg)
    muscle_seg_imgs = get_mask_slices_from_volume(muscle_seg)
    detection_imgs = get_slices_from_volume(detection_array, lung_seg)
    # detection_imgs = get_mask_slices_from_volume(detection_array)

    all_imgs = list(zip(original_imgs, lung_seg_imgs, muscle_seg_imgs, detection_imgs))

    for idx in range(len(all_imgs)):

        vatVol_cm3 = fat_report_cm3[idx]['vatVol']
        satVol_cm3 = fat_report_cm3[idx]['satVol']

        st.text(f"Slice {idx + 1} / {len(all_imgs)}")
        st.text(f"Visceral volume {vatVol_cm3:.3f} cm3")
        st.text(f"Subcutaneous volume {satVol_cm3:.3f} cm3")

        img_tuple = all_imgs[idx]
        img_list = list(img_tuple)
        st.image(img_list, caption=["Volume", "Lung Mask", "Muscle Mask", "Detection Boxes"])



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


def display_volume_and_mask(original_array, segmentation_array):


    num_labels = segmentation_array.max()
    imgs = []
    cm = plt.get_cmap('gray')
    cm_hot = plt.get_cmap('inferno')  # copper
    zd, yd, xd = original_array.shape
    # for i in range(zd):
    for i in range(2):
        mskmax = original_array[segmentation_array > 0].max()
        mskmin = original_array[segmentation_array > 0].min()
        im_arr = (original_array[i, :, :].astype(float) - mskmin) * (1.0 / (mskmax - mskmin))
        im_arr_copy = np.copy(im_arr)
        im_arr_copy = np.uint8(im_arr_copy)
        im_arr = np.uint8(cm(im_arr) * 255)
        im = Image.fromarray(im_arr).convert('RGBA')
        imgs.append(im.resize((150, 150)))

        print(segmentation_array[i][0][0])

        # seg_with_vol = np.where(segmentation_array[i] == 0, original_array[i], segmentation_array[i])
        mask_arr = np.uint8(cm_hot(segmentation_array[i, :, :].astype(float) / num_labels) * 255)
        # mask_arr = np.uint8(cm_hot(seg_with_vol.astype(float) / num_labels) * 255)


        # mask_arr = np.where(segmentation_array[i] != 0, mask_arr, im_arr)

        mask = Image.fromarray(mask_arr).convert('RGBA')
        # black = (0, 0, 3)

        # mask_np = np.asarray(mask.getdata())
        # print("unique mask np", np.unique(mask_np))

        # mask_data = [(0, 0, 0, 0) if item[:3] == black else item for item in mask.getdata()]
        # mask.putdata(mask_data)
        # mask = Image.fromarray(mask_arr)

        # TODO fix
        mask = Image.blend(im, mask, alpha=0.5)
        # red = Image.new('RGB', im.size, (255, 0, 0))
        # mask = Image.composite(im, red, mask).convert('RGB')



        imgs.append(mask.resize((150, 150)))

    st.image(imgs)


def lesion_detect(source_file):
    print("lesion detect called with", source_file)

    if segmenter.is_nifti(source_file):
        attention_volume, detection_volume = segmenter.covid_detector_nifti(source_file)
    else:
        attention_volume, detection_volume = segmenter.covid_detector_dcm(source_file)

    # TODO display volumes


def lesion_detect_seg(source_file):
    print("lesion detect seg called with", source_file)

    if segmenter.is_nifti(source_file):
        mask_volume, detection_volume = segmenter.covid_detector_seg_nifti(source_file)
    else:
        mask_volume, detection_volume = segmenter.covid_detector_seg_dcm(source_file)

    # TODO display volumes


def lungmask_segment(source_dir):
    print(filename)
    segmentation, input_nda, spx, spy, spz = segmenter.lungmask_segment(source_dir, model_name='R231CovidWeb')
    display_lungmask_segmentation(segmentation, input_nda, spx, spy, spz)

    # display_volume_and_mask(input_nda, output_nda)

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

    ##### File Selector #####
    #TODO upload of several (DICOM) files needs the streamlit dev version, which is difficult to use
    st.header("Please Upload the Chest CT Nifti here")
    # uploaded_file = st.file_uploader(label="", type=["nii", "nii.gz"])
    # TODO allow nii as well
    uploaded_file = st.file_uploader(label="", type=["nii.gz"])

    ##### File Selector #####

    ##### XNAT connection #####
    #this is behind a VPN so you need to connect your own XNAT

    xnat_working = True
    try:
        with xnat.connect('http://armada.doc.ic.ac.uk/xnat-web-1.7.6', user="admin", password="admin") as session:

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
    except:
        xnat_working = False

    # TODO removing hardcoing of available containers
    # TODO have better names

    worker_methods, worker_names = get_worker_information()

    workers_selected = st.multiselect('Containers', worker_names)


    if st.button('download and analyse'):
        latest_iteration = st.empty()

        if xnat_working:
            bar = st.progress(0)

            shared_dir = os.environ.get('DATA_SHARE_PATH', '')

            dir_ = os.path.join('/tmp/', subject_name)
            scan.download_dir(dir_, verbose=True)
            download_dir = ''
            for path in Path(dir_).rglob('*.dcm'):
                download_dir, file = os.path.split(str(path.resolve()))
                break
            bar.progress(100)

            st.text('Analysis progress...')
            bar2 = st.progress(0)

            # without bar
            filename = os.path.join(download_dir, file)

            source_dir = move_files_to_shared_directory(download_dir)
        else:
            print(uploaded_file)
            # writing file to disk
            # this is docker specific
            # TODO allow for .nii as well

            file_type = ".nii.gz"
            filename = os.path.join(os.environ['DATA_SHARE_PATH'], "input" + file_type)

            with open(filename, "wb") as f:
                f.write(uploaded_file.getbuffer())

            source_dir = os.path.split(filename)[1]

        threads = []
        for worker in workers_selected:
            thread = Thread(target=worker_methods[worker], args=(source_dir,))

            threads.append(thread)

            # add streamlit context information to the thread
            add_report_ctx(thread)
            thread.start()

        for thread in threads:
            thread.join()


        from workers.nifti_reader import read_nifti_image

        volume = read_nifti_image("/app/source/converted-case001.nii.gz")
        muscle_mask = read_nifti_image("/app/source/muscle_segment_converted_case001.nii.gz")
        detection_volume = read_nifti_image("/app/source/covid_lesion_detection_output/detection_converted-case001.nii.gz")

        volume_array = sitk.GetArrayFromImage(volume)
        muscle_mask_array = sitk.GetArrayFromImage(muscle_mask)
        detection_volume_array = sitk.GetArrayFromImage(detection_volume)

        print("volum dimensions", volume_array.shape)
        print("muscle mask dimension", muscle_mask_array.shape)
        print("detection vol dimensions", detection_volume_array.shape)

        lung_mask_array = np.load("/app/source/lungmask_seg_converted_case001.npy")

        fat_report = read_csv("/app/source/fat_report_converted_case001.txt")


        print("fat report len", len(fat_report))
        fat_report_cm3 = convert_report_to_cm3(fat_report)
        # display_volume_and_slice_information(volume_array, lung_mask_array, muscle_mask_array,
        #                                          detection_volume_array, fat_report_cm3)



    ##### XNAT connection #####

    ##### Output Area #####
    #st.header("Result:")
    #st.subheader("Probability of Covid-19 infection=96.5%")
    #st.subheader("Covid-19 severity index: 1")

    ##### Output Area #####
    #st.image([lung, seg])

