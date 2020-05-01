import streamlit as st
from plotter import generateHUplots
import numpy as np
import SimpleITK as sitk

class LungmaskSegmentationDisplayer:

    def __init__(self, original_array, segmentation_array):
        self.original_array = original_array
        self.segmentation_array = segmentation_array


    def display(self):
        input_nifti = sitk.GetImageFromArray(self.original_array)
        spx, spy, spz = input_nifti.GetSpacing()

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
