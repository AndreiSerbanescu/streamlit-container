import streamlit as st
from plotter import generateHUplots
import numpy as np
import SimpleITK as sitk
from workers.nifti_reader import *
import os

class LungmaskSegmentationDisplayer:

    def __init__(self, original_nifti_path, segmentation_nifti_path):
        self.original_path = original_nifti_path
        self.segmentation_path = segmentation_nifti_path

        self.original_nifti = read_nifti_image(self.original_path)
        self.segmentation_nifti = read_nifti_image(self.segmentation_path)

        self.original_array     = sitk.GetArrayFromImage(self.original_nifti)
        self.segmentation_array = sitk.GetArrayFromImage(self.segmentation_nifti)

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
        st.markdown(self.__get_original_volume_download_link(), unsafe_allow_html=True)
        st.markdown(self.__get_segmentation_volume_download_link(), unsafe_allow_html=True)

    def get_arrays(self):
        return self.original_array, self.segmentation_array

    def __get_original_volume_download_link(self):
        file_server_port = os.environ["FILESERVER_PORT"]
        resource_name = os.path.split(self.original_path)[1]
        file_server_url = f"http://127.0.0.1:{file_server_port}/{resource_name}"
        return f'<a href="{file_server_url}" target="_blank" title="Original Nifti Volume">Download Original volume</a>'

    def __get_segmentation_volume_download_link(self):

        file_server_port = os.environ["FILESERVER_PORT"]
        resource_name = os.path.split(self.segmentation_path)[1]
        file_server_url = f"http://127.0.0.1:{file_server_port}/{resource_name}"
        return f'<a href="{file_server_url}" target="_blank" title="Segmentation Nifti Volume">Download Segmentation volume</a>'
