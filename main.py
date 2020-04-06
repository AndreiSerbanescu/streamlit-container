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
    #st.header("Please Upload the Chest CT Nifti here")
    #st.file_uploader(label="", type=["nii", "nii.gz"])
    ##### File Selector #####

    ##### XNAT connection #####
    #this is behind a VPN so you need to connect your own XNAT
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

        if st.button('download and analyse'):
            latest_iteration = st.empty()
            bar = st.progress(0)

            shared_dir = os.environ['DATA_SHARE_PATH']

            # TODO this is slightly hardcoded
            # TODO relies on the fact that both containers have the same path for the shared dir
            dir_ = os.path.join('{}/tmp/'.format(shared_dir), subject_name)
            scan.download_dir(dir_, verbose=True)
            download_dir = ''
            for path in Path(dir_).rglob('*.dcm'):
                download_dir, file = os.path.split(str(path.resolve()))
                break
            bar.progress(100)

            st.text('Analysis progress...')
            bar2 = st.progress(0)

            # model = lungmask.get_model('unet', 'R231CovidWeb')
            # input_image = utils.get_input_image(download_dir)
            # input_nda = sitk.GetArrayFromImage(input_image)
            # print(input_nda.shape)
            # zd, yd, xd = input_nda.shape
            #
            # spx, spy, spz = input_image.GetSpacing()
            # result = lungmask.apply(input_image, model, bar2, force_cpu=False, batch_size=20, volume_postprocessing=False)


            # without bar
            filename = os.path.join(download_dir, file)
            print(filename)
            result = segmenter.lungmask_segment(filename, model_name='R231CovidWeb')

            print("Result is:")
            print(result)

            result_out = sitk.GetImageFromArray(result)
            # result_out.CopyInformation(input_image)
            sitk.WriteImage(result_out, os.path.join(dir_, 'segmentation.nii.gz'))
            bar2.progress(100)

            output_nda = sitk.GetArrayFromImage(result_out)
            st.header("HU distribution:")
            generateHUplots.generateHUPlots(input_nda, output_nda, 2)
        
            right = np.count_nonzero(output_nda==1)*spx*spy*spz
            left = np.count_nonzero(output_nda==2)*spx*spy*spz
            print(right)
            print(left)

            st.header("Result:")
            st.header(f'right lung: {right} mm\N{SUPERSCRIPT THREE}')
            st.header(f'left lung: {left} mm\N{SUPERSCRIPT THREE}')

            st.markdown('**Segmentation by:** Johannes Hofmanninger, Forian Prayer, Jeanny Pan, Sebastian Röhrich, \
                Helmut Prosch and Georg Langs. "Automatic lung segmentation in routine imaging \
                is a data diversity problem, not a methodology problem". 1 2020, \
                [https://arxiv.org/abs/2001.11767](https://arxiv.org/abs/2001.11767)')

            num_labels = output_nda.max()
            imgs = []
            cm = plt.get_cmap('gray')
            cm_hot = plt.get_cmap('inferno') #copper
            for i in range(zd):
                mskmax = input_nda[output_nda > 0].max()
                mskmin = input_nda[output_nda > 0].min()
                im = (input_nda[i,:,:].astype(float) - mskmin) * (1.0/(mskmax - mskmin))
                im = np.uint8(cm(im) * 255)   
                im = Image.fromarray(im).convert('RGB')
                imgs.append(im.resize((150, 150)))
                im = np.uint8(cm_hot(output_nda[i,:,:].astype(float) / num_labels) * 255)  
                im = Image.fromarray(im).convert('RGB')
                imgs.append(im.resize((150, 150)))

            st.image(imgs)

    ##### XNAT connection #####

    ##### Output Area #####
    #st.header("Result:")
    #st.subheader("Probability of Covid-19 infection=96.5%")
    #st.subheader("Covid-19 severity index: 1")

    ##### Output Area #####
    #st.image([lung, seg])

