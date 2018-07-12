# Initialize the image
FROM python:2
MAINTAINER Jonathan Marty <jonathan.n.marty@gmail.com>

# Expose ports
EXPOSE 8081 8081
EXPOSE 8082 8082
# This is the port for the "sandbox" feature, which is not implemented yet
#EXPOSE 8083 8083

# Set up directories
ADD . /ffbo.processor
RUN git clone --single-branch -b local_build https://github.com/fruitflybrain/ffbo.neuronlp /ffbo.neuronlp
RUN git clone https://github.com/fruitflybrain/ffbo.lib /ffbo.neuronlp/lib
RUN git clone https://github.com/fruitflybrain/ffbo.neurogfx /ffbo.neurogfx
RUN git clone https://github.com/fruitflybrain/ffbo.lib /ffbo.neurogfx/lib

# Set environment variables
ENV HOME /
ENV DEBIAN_FRONTEND noninteractive

# Crossbar.io connection defaults
ENV CBURL ws://crossbar:8080/ws
ENV CBREALM realm1

# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted] && pip install crossbar==17.12.1

# install ffbo.processor dependecies
RUN pip install numpy
RUN pip install pandas
RUN pip install beautifulsoup4
RUN pip install tinydb
RUN pip install simplejson

# Install SMTP mail server
RUN apt-get update
RUN apt-get install -y sendmail

# Create config file
RUN python ffbo.processor/config.py --nlp-path /ffbo.neuronlp --gfx-path /ffbo.neurogfx --path ffbo.processor/components/.crossbar/ --filename docker_config.json

# Run server
CMD sh ffbo.processor/components/run_server.sh docker_config.json
