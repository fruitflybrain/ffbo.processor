# Initialize the image
FROM python:2
MAINTAINER Yiyin Zhou <yiyin@ee.columbia.edu>

# Set up directories
RUN git clone https://github.com/fruitflybrain/ffbo.processor /ffbo.processor
RUN git clone --single-branch -b hemibrain https://github.com/fruitflybrain/ffbo.neuronlp /ffbo.neuronlp

RUN mkdir /ffbo.neuronlp/img/flycircuit
RUN git clone --single-branch -b hemibrain https://github.com/fruitflybrain/ffbo.lib /ffbo.neuronlp/lib
RUN git clone https://github.com/fruitflybrain/ffbo.neurogfx /ffbo.neurogfx
RUN git clone --single-branch -b hemibrain https://github.com/fruitflybrain/ffbo.lib /ffbo.neurogfx/lib

# Set environment variables
ENV HOME /
ENV DEBIAN_FRONTEND noninteractive

# Crossbar.io connection defaults
ENV CBURL ws://crossbar:8080/ws
ENV CBREALM realm1

# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted]==18.12.1 && pip install crossbar==17.12.1

# install ffbo.processor dependecies
RUN pip install numpy==1.14.5
RUN pip install pandas
RUN pip install beautifulsoup4
RUN pip install tinydb
RUN pip install simplejson
RUN pip install configparser

# Install SMTP mail server
RUN apt-get update
RUN apt-get install -y sendmail

WORKDIR /ffbo.processor/components

SHELL ["bash", "-c"]

# Run server
CMD sh run_server.sh docker_config.json
