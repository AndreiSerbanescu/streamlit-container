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

RUN apt-get install curl -y #debugging
RUN apt-get install vim -y #debugging

# Install dependencies for generating report
RUN pip3 install pandoc

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y texlive-latex-base
RUN apt-get install -y texlive-latex-extra
RUN apt-get install -y texlive-pictures
RUN apt-get install -y texlive-fonts-recommended
RUN pip3 install pdflatex

RUN mkdir /app/src
COPY files/ /app/src/