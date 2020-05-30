from common_display.plotter import generateHUplots
import numpy as np
import SimpleITK as sitk
from common_display.nifti_reader import *
import os
from common_display.display.download_button import DownloadDisplayer
try:
    import streamlit
except ImportError:
    pass


class LungmaskSegmentationDisplayer:

    def __init__(self, original_nifti_path, segmentation_nifti_path, download_displayer=None, streamlit_wrapper=None):

        if segmentation_nifti_path is None:
            self.segmentation_nifti = None
            return

        self.st = streamlit if streamlit_wrapper is None else streamlit_wrapper

        self.original_path = original_nifti_path
        self.segmentation_path = segmentation_nifti_path

        self.original_nifti = read_nifti_image(self.original_path)
        self.segmentation_nifti = read_nifti_image(self.segmentation_path)

        self.original_array     = sitk.GetArrayFromImage(self.original_nifti)
        self.segmentation_array = sitk.GetArrayFromImage(self.segmentation_nifti)

        self.download_displayer = download_displayer if download_displayer is not None \
            else DownloadDisplayer(streamlit_wrapper=self.st)

    def display(self):

        if self.segmentation_nifti is None:
            return

        spx, spy, spz = self.original_nifti.GetSpacing()

        self.st.header("HU distribution:")
        generateHUplots.generateHUPlots(self.original_array, self.segmentation_array, 2, streamlit_wrapper=self.st)

        right = np.count_nonzero(self.segmentation_array == 1) * spx * spy * spz
        left = np.count_nonzero(self.segmentation_array == 2) * spx * spy * spz

        self.st.header("Result:")
        self.st.header(f'right lung: {right} mm\N{SUPERSCRIPT THREE}')
        self.st.header(f'left lung: {left} mm\N{SUPERSCRIPT THREE}')

        self.st.markdown('**Lung Segmentation by:** Johannes Hofmanninger, Forian Prayer, Jeanny Pan, Sebastian Röhrich, \
                            Helmut Prosch and Georg Langs. "Automatic lung segmentation in routine imaging \
                            is a data diversity problem, not a methodology problem". 1 2020, \
                            [https://arxiv.org/abs/2001.11767](https://arxiv.org/abs/2001.11767)')

    def download_button(self):
        if self.segmentation_nifti is None:
            return

        self.download_displayer.display(os.path.split(self.segmentation_path)[1], "Lung segmentation mask")

    def get_seg_array(self):

        if self.segmentation_nifti is None:
            return None

        return self.segmentation_array
