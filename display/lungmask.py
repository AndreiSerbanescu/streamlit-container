import streamlit as st
from plotter import generateHUplots
import numpy as np
import SimpleITK as sitk
from workers.nifti_reader import *

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

        print("original volume spacing", spx, spy, spz)

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

        pass
        # if st.button("Download Input volume as Nifti"):
        # st.markdown(self.__get_original_volume_download_link(), unsafe_allow_html=True)

        # if st.button("Download Segmentation nifti volume"):
        # st.markdown(self.__get_segmentation_volume_download_link(), unsafe_allow_html=True)

    def get_arrays(self):
        return self.original_array, self.segmentation_array

    def __get_original_volume_download_link(self):
        # csv = df.to_csv(index=False)
        import pybase64
        b64 = pybase64.b64encode(
            self.original_nifti
        ).decode()  # some strings <-> bytes conversions necessary here
        
        # href = f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
        # return f'<a href="data:file/nii.gz" download="{self.original_nifti}">Download Nifti volume</a>'
        return f'<a href="data:file/nii.gz;{b64}">Download csv file</a>'

    def __get_segmentation_volume_download_link(self):
        # return f'<a href="data:file/nii.gz" download="{self.segmentation_nifti}">Download Nifti volume</a>'
        return ''