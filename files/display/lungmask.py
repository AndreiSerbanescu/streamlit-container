import streamlit as st
from plotter import generateHUplots
import numpy as np
import SimpleITK as sitk
from workers.nifti_reader import *
import os
from display.download_button import DownloadDisplayer

class LungmaskSegmentationDisplayer:

    def __init__(self, original_nifti_path, segmentation_nifti_path, download_displayer=None):
        self.original_path = original_nifti_path
        self.segmentation_path = segmentation_nifti_path

        self.original_nifti = read_nifti_image(self.original_path)
        self.segmentation_nifti = read_nifti_image(self.segmentation_path)

        self.original_array     = sitk.GetArrayFromImage(self.original_nifti)
        self.segmentation_array = sitk.GetArrayFromImage(self.segmentation_nifti)

        self.download_displayer = download_displayer if download_displayer is not None else DownloadDisplayer()

    def display(self):
        spx, spy, spz = self.original_nifti.GetSpacing()

        st.header("HU distribution:")
        generateHUplots.generateHUPlots(self.original_array, self.segmentation_array, 2)

        right = np.count_nonzero(self.segmentation_array == 1) * spx * spy * spz
        left = np.count_nonzero(self.segmentation_array == 2) * spx * spy * spz

        st.header("Result:")
        st.header(f'right lung: {right} mm\N{SUPERSCRIPT THREE}')
        st.header(f'left lung: {left} mm\N{SUPERSCRIPT THREE}')

        st.markdown('**Lung Segmentation by:** Johannes Hofmanninger, Forian Prayer, Jeanny Pan, Sebastian Röhrich, \
                            Helmut Prosch and Georg Langs. "Automatic lung segmentation in routine imaging \
                            is a data diversity problem, not a methodology problem". 1 2020, \
                            [https://arxiv.org/abs/2001.11767](https://arxiv.org/abs/2001.11767)')

    def download_button(self):
        self.download_displayer.display(os.path.split(self.original_path)[1], "Original volumetric image")
        self.download_displayer.display(os.path.split(self.segmentation_path)[1], "Lung segmentation mask")

    def get_arrays(self):
        return self.original_array, self.segmentation_array