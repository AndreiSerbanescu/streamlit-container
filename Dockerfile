FROM nvidia/cuda:latest

WORKDIR /app

# Installing Python3 and Pip3
RUN apt-get update
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install setuptools pip --upgrade --force-reinstall


RUN pip3 install streamlit
RUN pip3 install sklearn
RUN pip3 install xnat
RUN pip3 install matplotlib
RUN pip3 install SimpleITK

ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
RUN apt-get install -y locales && locale-gen en_US.UTF-8

RUN apt-get install curl -y #debugging
RUN apt-get install vim -y #debugging

RUN mkdir /app/src
COPY files/ /app/src/