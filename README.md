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
