# FFBO Processor Component
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

    docker run -P -t --net ffbonet --name ffbo.processor jonmarty/ffbo.processor


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

    docker run -P -it --net ffbonet --name ffbo.processor ffbo/processor:develop bash

Running the server is done with:

    sh ffbo.processor/components/run_server.sh docker_config.json

or

    cd ffbo.processor/components
    crossbar start --config docker_config.json

This will launch the router, processor and web interface on port 8080 or the local server. Details of the crossbar config can be seen in .crossbar/config.json
