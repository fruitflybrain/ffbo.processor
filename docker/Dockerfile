###########################################
# run using: docker build -t ffbo/proessor_component:develop .
# build using : docker run --name processor_component -v $(dirname `pwd`):/processor_component  -p 8080:8080 -p 8081:8081 -p 8082:8082 -it ffbo/processor_component:develop sh /processor_component/components/run_server.sh
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

# Install SMTP mail server
RUN apt-get update
RUN apt-get install -y sendmail
