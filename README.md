## Synopsis

This package acts as multple important parts of the FFBO web infrastruture, it contails:
* The Crossbar WAMP router
* The FFBO processor
* The Web User Interface

## Execution

As the main router, this should be started with the following command in the /processor_component/processor_component/ directory:

	crossbar start
	
This will launch the router, processor and web interface on port 8080 or the local server. Details of the crossbar config can be seen in .crossbar/config.json

## Motivation

Currently this main package contains three distinct elements, in time this will be broken out into

* A generic crossbar router
* A web server
* A processor server

## Installation

This project requires crossbario[twisted]. This service can also be launched by building the docker and launching:

	docker run -it ffbo/processor crossbar start

### Docker Hub

Installing via the Docker Hub repository (https://hub.docker.com/r/jonmarty/ffbo.processor) is recommended for non-developers. The image is installed directly onto your local Docker daemon, from which you can run it in a container. Installation is as follows:

    docker pull jonmarty/ffbo.processor

Once the image is installed, you can run it in a container:

    docker run --net ffbonet --name ffbo.processor jonmarty/ffbo.processor


### Github with Docker Compose

Installing via the Github repository (https://github.com/jonmarty/ffbo.processor) is recommended for developers.The code is downloaded as follows:

    git clone https://github.com/jonmarty/ffbo.processor

Building and running the repository is simplified with Docker Compose, which stores the configuration for a service (such as network and name for the container and the Dockerfile to build from) in a docker-compose.yml file, simplifying the command-line call. Building and running the Docker image can be accomplished with:

    docker-compose build <service-name>
    docker-compose run <service-name>

Note that the container can be both built and run with the following command:

    docker-compose up <service-name>

