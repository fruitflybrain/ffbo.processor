DOCKER_PROCESSOR_PATH="/ffbo.processor"
DOCKER_NLP_PATH="/ffbo.neuronlp"
DOCKER_GFX_PATH="/ffbo.neurogfx"

LOCAL_NLP_PATH="$(dirname `pwd`)/../ffbo.neuronlp"
LOCAL_GFX_PATH="$(dirname `pwd`)/../ffbo.neurogfx"

python $(dirname `pwd`)/config.py --nlp-path $DOCKER_NLP_PATH --gfx-path $DOCKER_GFX_PATH --path $(dirname `pwd`)/components/.crossbar/ --filename docker_config.json

docker rm ffbo.processor
docker run --name ffbo.processor -v $(dirname `pwd`):$DOCKER_PROCESSOR_PATH -v $LOCAL_NLP_PATH:$DOCKER_NLP_PATH -v $LOCAL_GFX_PATH:$DOCKER_GFX_PATH -p 8080:8080 -p 8081:8081 -p 8082:8082 -it ffbo/processor:develop sh $DOCKER_PROCESSOR_PATH/components/run_server.sh docker_config.json
