import streamlit as st
import numpy as np
import xnat
import os
from pathlib import Path
import subprocess as sb
import requests
from common_display.display.main_displayer import MainDisplayer
from common import utils
from commander.commander import CommanderHandler
import shutil

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


def copy_files_to_shared_directory(source_dir):

    data_share = os.environ["DATA_SHARE_PATH"]

    unique_id = utils.get_unique_id()
    input = "streamlit_input" + unique_id
    abs_input_path = os.path.join(data_share, input)

    if not os.path.exists(abs_input_path):
        os.mkdir(abs_input_path)

    cp_cmd = "cp -r {} {}".format(source_dir, abs_input_path)
    exit_code = sb.call([cp_cmd], shell=True)

    if exit_code == 1:
        raise Exception("Couldn't move input files from {} to {}".format(source_dir, abs_input_path))

    return os.path.join(input, "files")


def start_download_and_analyse(source_dir, workers_selected, email_address, subject_name="", fat_interval=None):

    if len(workers_selected) == 0:
        st.markdown("**Need to select at least one container**")
        return

    commander_share_path = os.environ["COMMANDER_AND_STREAMLIT_SHARE_PATH"]
    config_in_dir = os.path.join(commander_share_path, "config")
    result_dir = os.path.join(commander_share_path, "result")

    ch = CommanderHandler(config_in_dir, result_dir, email_receiver=email_address)
    paths, workers_not_ready, workers_failed \
        = ch.call_commander(subject_name, source_dir, workers_selected, fat_interval)

    lungmask_path = paths.get("lungmask")
    input_path = paths.get("input")
    fat_report_path = paths.get("fat_report")
    muscle_seg_path = paths.get("muscle_seg")
    lesion_detection_path = paths.get("lesion_detection")
    lesion_attention_path = paths.get("lesion_attention")
    lesion_seg_mask_path = paths.get("lesion_seg_mask")
    lesion_seg_detection_path = paths.get("lesion_seg_detection")


    if email_address is None:
        st.text("No email sent")
    else:
        st.text(f"Email with report sent to {email_address}")


    workers_unsuccessful = workers_not_ready + workers_failed
    if len(workers_unsuccessful) > 0:
        st.text("The following workers were unsuccessful:")
        for worker in workers_unsuccessful:
            st.text(worker)
        st.text('')

    display_report(input_path, lungmask_path, muscle_seg_path, lesion_detection_path, lesion_attention_path,
                   lesion_seg_detection_path, lesion_seg_mask_path, fat_report_path, fat_interval)


def display_report(input_path, lungmask_path, muscle_seg_path, lesion_detection_path, lesion_attention_path,
                   lesion_seg_detection_path, lesion_seg_mask_path, fat_report_path, fat_interval):

    if input_path is None:
        st.markdown("**Internal error occured - cannot display**")
        return


    main_displayer = MainDisplayer(save_to_pdf=False)

    main_displayer.display_volume_and_slice_information(input_path, lungmask_path, muscle_seg=muscle_seg_path,
                                                        lesion_detection=lesion_detection_path,
                                                        lesion_attention=lesion_attention_path,
                                                        lesion_detection_seg=lesion_seg_detection_path,
                                                        lesion_mask_seg=lesion_seg_mask_path,
                                                        fat_report=fat_report_path,
                                                        fat_interval=fat_interval)


def __display_worker_not_ready(hostname, streamlit_wrapper=None):
    import streamlit

    st_wrap = streamlit_wrapper if streamlit_wrapper is not None else streamlit
    st_wrap.markdown(f"**{hostname} worker didn't start properly**")

def __display_worker_failed(hostname, streamlit_wrapper=None):
    import streamlit

    st_wrap = streamlit_wrapper if streamlit_wrapper is not None else streamlit
    st_wrap.markdown(f"**{hostname} worker failed**")

def download_and_analyse_button_xnat(subject_name, scan, workers_selected, email_address, fat_interval=None,
                                     send_email=False):

    if st.button('download and analyse', key="xnat-download-button"):
        latest_iteration = st.empty()

        if email_address == "":
            st.markdown('## No email address specified - no email will be sent')

            if send_email:
                st.markdown("## Please tick *Don't send email* if you wish to continue")
                return

        bar = st.progress(0)

        tmp_dir_name = subject_name + "-" + utils.get_unique_id()

        dir_ = os.path.join('/tmp/', tmp_dir_name)
        scan.download_dir(dir_, verbose=True)
        download_dir = ''
        for path in Path(dir_).rglob('*.dcm'):
            download_dir, file = os.path.split(str(path.resolve()))
            break
        bar.progress(100)

        st.text('Analysis progress...')

        source_dir = copy_files_to_shared_directory(download_dir)

        # delete input files from tmp directory
        shutil.rmtree(os.path.join("/tmp", tmp_dir_name))

        start_download_and_analyse(source_dir, workers_selected, email_address, subject_name=subject_name,
                                   fat_interval=fat_interval)



def download_and_analyse_button_upload(uploaded_file, workers_selected, email_address, subject_name,
                                       fat_interval=None, send_email=False):

    if st.button('download and analyse', key="uploaded download button"):
        file_type = ".nii.gz"
        unique_id = utils.get_unique_id()
        filename = os.path.join(os.environ['DATA_SHARE_PATH'], "input" + unique_id + file_type)

        with open(filename, "wb") as f:
            try:
                f.write(uploaded_file.getbuffer())
            except:
                st.markdown("## No file uploaded**")
                return

        if subject_name == "":
            st.markdown("## Please enter subject name")
            return

        if email_address == "":
            st.markdown('## No email address specified - no email will be sent')

            if send_email:
                st.markdown("## Please tick *Don't send email* if you wish to continue")
                return

        source_dir = os.path.split(filename)[1]

        start_download_and_analyse(source_dir, workers_selected, email_address, subject_name=subject_name,
                                   fat_interval=fat_interval)

def get_worker_names():
    return [LUNGMASK_SEGMENT, CT_FAT_REPORT, CT_MUSCLE_SEGMENTATION,
            LESION_DETECTION, LESION_DETECTION_SEG]

def worker_selection():
    # worker_methods, worker_names = get_worker_information()
    worker_names = get_worker_names()

    # worker_names.remove(LUNGMASK_SEGMENT)

    # st.text("Running lungmask segmentation by default")
    workers_selected = st.multiselect('Containers', worker_names)

    # lungmask segment runs by default
    # workers_selected.append(LUNGMASK_SEGMENT)
    return workers_selected


if __name__ == "__main__":

    #### Page Header #####
    # st.title("CoCaCoLA - The Cool Calculator for Corona Lung Assessment")
    st.title("CoViD-19 Risk Calculator")  # for more formal occasions :S
    st.title("NOT FOR CLINICAL USE")
    pcr_positive = st.checkbox("PCR Positive?")
    seropositive = st.checkbox("Seropositive?")

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
        xnat_address = 'http://armada.doc.ic.ac.uk/xnat-web-1.7.6'
        xnat_user = "admin"
        xnat_password = "admin"

        try:
            with xnat.connect(xnat_address, user=xnat_user, password=xnat_password) as session:

                #pn = [x.name for x in session.projects.values()]
                pn = ["COVID-19"]

                project_name = st.selectbox('Project', pn)
                project = session.projects[project_name]

                sn = [x.label for x in project.subjects.values()]
                sn.remove("coronacases_org_001")
                
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

                dont_send_email = st.checkbox("Don't send email")
                email_address = None
                if not dont_send_email:
                    email_address = st.text_input("Enter email address for sending the report")

                workers_selected = worker_selection()

                if CT_FAT_REPORT in workers_selected:
                    st.text("Select portion of lung CT to calculate the adipose tissue volumes")
                    st.text("From 0 (bottom of thorax) to 100 (top of thorax)")
                    fat_interval = st.slider("Fat report slider", .0, 100.0, (25.0, 75.0))

                    download_and_analyse_button_xnat(subject_name, scan, workers_selected, email_address,
                                                     fat_interval=fat_interval, send_email=not dont_send_email)
                else:
                    download_and_analyse_button_xnat(subject_name, scan, workers_selected, email_address,
                                                     send_email=not dont_send_email)

        except requests.exceptions.ConnectionError as e:
            st.text(f"xnat server {xnat_address} not working")
            print(f"xnat exception {e} {type(e)}")


    else:
        ##### File Selector #####
        st.header("Please Upload the Chest CT Nifti here")
        uploaded_file = st.file_uploader(label="", type=["nii.gz"])
        subject_name = st.text_input("Enter name of subject")

        dont_send_email = st.checkbox("Don't send email")
        email_address = None
        if not dont_send_email:
            email_address = st.text_input("Enter email address for sending the report")

        workers_selected = worker_selection()

        if CT_FAT_REPORT in workers_selected:
            st.text("Select portion of lung CT to calculate the adipose tissue volumes")
            st.text("From 0 (bottom of thorax) to 100 (top of thorax)")
            fat_interval = st.slider("Fat report slider", .0, 100.0, (25.0, 75.0))

            download_and_analyse_button_upload(uploaded_file, workers_selected, email_address, subject_name,
                                               fat_interval=fat_interval, send_email=not dont_send_email)
        else:
            download_and_analyse_button_upload(uploaded_file, workers_selected, email_address, subject_name,
                                               send_email=not dont_send_email)

        ##### File Selector #####

    # start_thread_test_delete_this()
    ##### XNAT connection #####

