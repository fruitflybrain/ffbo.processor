###########################################
# build using :  docker build -t ffbo/processor:develop .
###########################################
FROM python:2

MAINTAINER Adam Tomkins <a.tomkins@sheffield.ac.uk>

ADD . /ffbo.processor
#ADD ffbo.neuronlp /ffbo.neuronlp
#ADD ffbo.lib /ffbo/neuronlp/lib
#ADD ffbo.neurogfx /ffbo.neurogfx
#ADD ffbo.lib /ffbo.neurogfx/lib

RUN apt-get update
RUN apt-get install -y --force-yes git

RUN git clone https://github.com/fruitflybrain/ffbo.neuronlp /ffbo.neuronlp
RUN git clone https://github.com/fruitflybrain/ffbo.neurogfx /ffbo.neurogfx
RUN git clone https://github.com/fruitflybrain/ffbo.lib /ffbo.neuronlp/lib
RUN git clone https://github.com/fruitflybrain/ffbo.lib /ffbo.neurogfx/lib

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

#Run the applcation
CMD python ffbo.processor/config.py --nlp-path ffbo.neuronlp --gfx-path ffbo.neurogfx --path ffbo.processor/components/.crossbar/ --filename docker_config.json
CMD sh ffbo.processor/components/run_server.sh docker_config.json
