###########################################
# run using: docker build -t ffbo/proessor .
# build using : docker run --name processor -p 8080:8080 -p 8081:8081 -p 8082:8082 -it ffbo/processor sh run_server.sh
###########################################
FROM python:2

MAINTAINER Adam Tomkins <a.tomkins@sheffield.ac.uk>

ENV HOME /app
ENV DEBIAN_FRONTEND noninteractive

# Crossbar.io connection defaults
ENV CBURL ws://crossbar:8080/ws
ENV CBREALM realm1

# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted] && pip install crossbar

RUN pip install numpy
RUN pip install pandas
RUN pip install beautifulsoup4

# Install SMTP mail server
RUN apt-get update
RUN apt-get install -y sendmail

# Install processor_component into the docker container
WORKDIR /app
RUN git clone https://github.com/fruitflybrain/ffbo.processor.git
WORKDIR /app/ffbo.processor
RUN python setup.py install

WORKDIR /app/ffbo.processor/components/
