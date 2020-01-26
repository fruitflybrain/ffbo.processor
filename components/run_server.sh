python /ffbo.processor/config.py --path /ffbo.processor/components/.crossbar/ --filename docker_config.json

cd /ffbo.neuronlp
git pull
cd /ffbo.processor/components

BASEDIR=$(dirname "$0")
cd $BASEDIR

# Decide which config to use based on first argument
if [ $# -eq 0 ]; then
    # use default configuration
    echo "Using default Configuration"
    crossbar start
else
    crossbar start --config $1
fi

/etc/init.d/sendmail start
