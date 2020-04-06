FROM nvidia/cuda:latest

WORKDIR /app

# Installing Python3 and Pip3
RUN apt-get update
RUN apt-get update && apt-get install -y python python-dev python3.7 python3.7-dev python3-pip virtualenv libssl-dev libpq-dev git build-essential libfontconfig1 libfontconfig1-dev
RUN pip3 install setuptools pip --upgrade --force-reinstall


RUN pip3 install streamlit
RUN pip3 install sklearn
RUN pip3 install xnat
RUN pip3 install dicom2nifti

COPY main.py /app/main.py
COPY plotter/__init__.py /app/plotter/__init__.py
COPY plotter/generateHUplots.py /app/plotter/generateHUplots.py
COPY lung.png /app/lung.png
COPY seg.png /app/seg.png
