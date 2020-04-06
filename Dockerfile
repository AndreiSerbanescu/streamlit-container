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
RUN pip3 install matplotlib
RUN pip3 install SimpleITK

ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
RUN apt-get install -y locales && locale-gen en_US.UTF-8

COPY main.py /app/main.py
COPY lungmask_docker.py /app/lungmask_docker.py
COPY plotter/__init__.py /app/plotter/__init__.py
COPY plotter/generateHUplots.py /app/plotter/generateHUplots.py
COPY lung.png /app/lung.png
COPY seg.png /app/seg.png
