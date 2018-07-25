# FFBO Processor Component
[![Twitter Follow](https://img.shields.io/twitter/follow/flybrainobs.svg?style=social&label=Follow)](https://twitter.com/flybrainobs) ![license](https://img.shields.io/github/license/jonmarty/ffbo.processor.svg?style=flat-square) ![GitHub last commit](https://img.shields.io/github/last-commit/jonmarty/ffbo.processor.svg?style=flat-square) [![Docker Build Status](https://img.shields.io/docker/build/jonmarty/ffbo.processor.svg?style=flat-square)](https://hub.docker.com/r/jonmarty/ffbo.processor)
## Overview
This package contains the main component of the [FFBO architecture](http://fruitflybrain.org/), the Processor. The processor uses the [NeuroNLP](http://github.com/jonmarty/ffbo.nlp_component) and [NeuroArch](http://github.com/jonmarty/ffbo.neuroarch_component) database components as backends for processing text queries and accessing neurophysiological data. It can additionally be attached to [FFBOLab](http://github.com/jonmarty/ffbolab) to improve processing speed by leveraging local computing resources (default is to use FFBO's servers). FFBOLab provides a GUI interface across ports 8081 and 8082 on the host machine's localhost. Port 8081 serves the NeuroNLP interface, while port 8082 serves the NeuroGFX interface.

This package acts as multiple important parts of the FFBO web infrastruture, it contains:
* The Crossbar WAMP router
* The FFBO processor
* The Web User Interface

### Plans

Currently this main package contains three distinct elements, in time this will be broken out into

* A generic crossbar router
* A web server
* A processor server

## Installation and Execution

Options for installing and running ffbo.processor are explained below.

__NOTE__ If you are using a Docker image to run ffbo.processor, you will need the 'ffbonet' network initialized. You can check to see if it exists via

    docker network ls

If it does not, it can be initialized via

    docker network create -d bridge ffbonet

Please note that the 'bridge' driver provides a network that is limited to the host machine's Docker daemon, so images within it cannot communicate with external docker hosts or Docker daemons. If you would like to communicate between computers, please use the 'overlay' driver

    docker network create -d overlay ffbonet

### Docker Hub

Installing via the [Docker Hub](https://hub.docker.com/r/jonmarty/ffbo.processor) repository is recommended for non-developers. The image is installed directly onto your local Docker daemon, from which you can run it in a container. Installation is as follows:

    docker pull jonmarty/ffbo.processor

Once the image is installed, you can run it in a container:

    docker run -p 8081:8081 -p 8082:8082 -t --net ffbonet --name ffbo.processor jonmarty/ffbo.processor


### Github with Docker Compose

Installing via the [Github](https://github.com/jonmarty/ffbo.processor) repository is recommended for developers.The code is downloaded as follows:

    git clone https://github.com/jonmarty/ffbo.processor

Building and running the repository is simplified with Docker Compose, which stores the configuration for a service (such as network and name for the container and the Dockerfile to build from) in a docker-compose.yml file, simplifying the command-line call. Building and running the Docker image can be accomplished with:

    docker-compose build
    docker-compose run

Note that the container can be both built and run with the following command:

    docker-compose up

### Manual Execution

Downloading and building the repository and image are accomplished the same as in the above section. Accessing the bash interface for the container can be accomplished with:

    docker run -p 8081:8081 -p 8082:8082 -it --net ffbonet --name ffbo.processor ffbo/processor:develop bash

Running the server is done with:

    sh ffbo.processor/components/run_server.sh docker_config.json

or

    cd ffbo.processor/components
    crossbar start --config docker_config.json

This will launch the router, processor and web interface on port 8080 or the local server. Details of the crossbar config can be seen in .crossbar/config.json

### Configuration

FFBO components are configured using .ini files. If you are building and running Docker images on your local computer from the Github repository (including Docker Compose), you can configure the NLP Component via the './config.ini' file in the main directory of this repository. However, if you are downloading images directly from Docker Hub, you will need to create a '.ffbolab' folder in your computer's home directory. Into this directory, place a .ini config file referring to this component. This can be done in one of two ways. Either copy the default config file from the main directory of this repository via:

    cp config.ini ~/.ffbo/config/ffb.processor.ini

or, in the case that you don't have this repository installed, via:

    wget -o ~/.ffbo/config/ffbo.processor.ini https://cdn.rawgit.com/jonmarty/ffbo.processor/master/config.ini

Once you have configured the .ini file, you can run it with:

    docker run -p 8081:8081 -p 8082:8082 -it --net ffbonet --name ffbo.processor -v ~/.ffbo/config:/config jonmarty/ffbo.processor

Or equivalently for other build methods. If you have configured a port, make sure to expose it by adding the '-p [INTERNAL PORT]:[EXTERNAL PORT]', where the internal port is the port you configured in the .ini file and the external port is the port on localhost that the output of the internal port is mapped to. Running without docker is the same process described above in the Manual Execution section.

