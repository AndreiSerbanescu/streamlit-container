from display.fat_report import FatReportDisplayer
from display.lungmask import LungmaskSegmentationDisplayer
from workers.nifti_reader import read_nifti_image
from PIL import Image
from matplotlib import pyplot as plt
import SimpleITK as sitk
from display.download_button import DownloadDisplayer
import os
import numpy as np
import streamlit as st

def display_volume_and_slice_information(input_nifti_path, lung_seg_path, muscle_seg=None, lesion_detection=None,
                                         lesion_attention=None, lesion_detection_seg=None,
                                         lesion_mask_seg=None, fat_report=None, fat_interval=None):

    assert input_nifti_path is not None
    assert lung_seg_path is not None

    lungmask_displayer = LungmaskSegmentationDisplayer(input_nifti_path, lung_seg_path)
    original_array, lung_seg = lungmask_displayer.get_arrays()

    # fat_report may be None, in which case fat_report_displayer doesn't display anything
    fat_report_displayer = FatReportDisplayer(original_array, lung_seg, fat_report, fat_interval=fat_interval)

    lungmask_displayer.download_button()
    fat_report_displayer.download_button()

    # may be None
    fat_report_cm3 = fat_report_displayer.get_converted_report()

    detection_array = None
    attention_array = None
    muscle_seg_array = None
    detection_seg_array = None
    mask_seg_array = None


    if lesion_detection is not None:
        detection_array = read_nifti_image(lesion_detection)
        detection_array = sitk.GetArrayFromImage(detection_array)

        detection_download_displayer = DownloadDisplayer()
        detection_download_displayer.display(os.path.split(lesion_detection)[1], "Lesion Detection Volume")

    if lesion_attention is not None:
        attention_array = read_nifti_image(lesion_attention)
        attention_array = sitk.GetArrayFromImage(attention_array)

        attention_download_displayer = DownloadDisplayer()
        attention_download_displayer.display(os.path.split(lesion_attention)[1], "Attention Volume")

    if muscle_seg is not None:
        muscle_seg_array = read_nifti_image(muscle_seg)
        muscle_seg_array = sitk.GetArrayFromImage(muscle_seg_array)

        muscle_download_displayer = DownloadDisplayer()
        muscle_download_displayer.display(os.path.split(muscle_seg)[1], "Muscle Segmentation")

    if lesion_detection_seg is not None:
        detection_seg_array = read_nifti_image(lesion_detection_seg)
        detection_seg_array = sitk.GetArrayFromImage(detection_seg_array)

        detection_seg_download_displayer = DownloadDisplayer()
        detection_seg_download_displayer.display(os.path.split(lesion_detection_seg)[1],
                                                 "Lesion Detection Segmentation")

    if lesion_mask_seg is not None:
        mask_seg_array = read_nifti_image(lesion_mask_seg)
        mask_seg_array = sitk.GetArrayFromImage(mask_seg_array)

        mask_seg_download_displayer = DownloadDisplayer()
        mask_seg_download_displayer.display(os.path.split(lesion_mask_seg)[1], "Lesion Detection Mask")

    lungmask_displayer.display()
    fat_report_displayer.display()

    __display_information_rows(original_array, lung_seg, muscle_seg_array, detection_array,
                               attention_array, detection_seg_array, mask_seg_array, fat_report_cm3)

def __display_information_rows(original_array, lung_seg, muscle_seg, detection_array, attention_array,
                               detection_seg_array, mask_seg_array, fat_report_cm3):


    if muscle_seg is not None:
        muscle_citation = "**Muscle Segmentation by:** Burns JE, Yao J, Chalhoub D, Chen JJ, Summers RM. A Machine" \
                          " Learning Algorithm to Estimate Sarcopenia on Abdominal CT. " \
                          "Academic Radiology 27:311–320 (2020)."\
                          "Graffy P, Liu J, Pickhardt PJ, Burns JE, Yao J, Summers RM. Deep Learning-Based Muscle Se" \
                          "gmentation and Quantification at Abdominal CT: Application to a longitudinal adult screen" \
                          "ing cohort for sarcopenia assessment. Br J Radiol 92:20190327 (2019)."\
                          "Sandfort V, Yan K, Pickhardt PJ, Summers RM. Data augmentation using generative" \
                          " adversarial networks (CycleGAN) to improve generalizability in CT segmentation tasks" \
                          ". Scientific Reports (2019) 9:16884."

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
        captions.append("Lesion Detection - Detection Boxes")

    if attention_array is not None:
        attention_imgs = get_slices_from_volume(attention_array, lung_seg)
        tuple_imgs.append(attention_imgs)
        captions.append("Lesion Detection - Attention")

    if detection_seg_array is not None:
        detection_seg_imgs = get_slices_from_volume(detection_seg_array, lung_seg)
        tuple_imgs.append(detection_seg_imgs)
        captions.append("Lesion Detection Segmentation - Detection Boxes")

    if mask_seg_array is not None:
        mask_seg_imgs = get_mask_slices_from_volume(mask_seg_array)
        tuple_imgs.append(mask_seg_imgs)
        captions.append("Lesion Detection Segmentation - Mask")

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
        st.image(img_list, caption=captions, width=250)

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
