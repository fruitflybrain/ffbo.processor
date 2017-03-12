###########################################
# build using :  docker build -t ffbo/processor:develop .
###########################################
FROM python:2

MAINTAINER Adam Tomkins <a.tomkins@sheffield.ac.uk>

ENV HOME /
ENV DEBIAN_FRONTEND noninteractive

# Crossbar.io connection defaults
ENV CBURL ws://crossbar:8080/ws
ENV CBREALM realm1

# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted] && pip install crossbar

# install ffbo.processor dependecies
RUN pip install numpy
RUN pip install pandas
RUN pip install beautifulsoup4
RUN pip install tinydb


# Install SMTP mail server
RUN apt-get update
RUN apt-get install -y sendmail
