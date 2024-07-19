#!/usr/bin/env bash
#FROM ubuntu:18.04 as base
FROM python:3.10-bullseye as base
ENV LANG en_US.UTF-8
ENV LANG C.UTF-8

RUN apt-get -y update  --fix-missing && apt-get install -y git
#RUN apt-get update && apt-get install -y software-properties-common gcc && add-apt-repository -y ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y python3-pip
#python3-distutils python3-pip python3-apt
COPY ./requirements.txt /requirements.txt

WORKDIR /
RUN ln -sfn /usr/bin/python3.10 /usr/bin/python
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools

RUN pip3 install -r requirements.txt --no-cache-dir

#RUN apt-get remove -y git && apt-get clean
