import os,sys
import argparse
import simplejson as json

from configparser import ConfigParser

# Grab configuration from file
root = os.path.expanduser("/")
home = os.path.expanduser("~")
filepath = os.path.dirname(os.path.abspath(__file__))
config_files = []
config_files.append(os.path.join(home, "config", "ffbo.processor.ini"))
config_files.append(os.path.join(root, "config", "ffbo.processor.ini"))
config_files.append(os.path.join(home, "config", "config.ini"))
config_files.append(os.path.join(root, "config", "config.ini"))
config_files.append(os.path.join(filepath, "config.ini"))
config = ConfigParser()
configured = False
for config_file in config_files:
    if os.path.exists(config_file):
        config.read(config_file)
        configured = True
        break
if not configured:
    raise Exception("No config file exists for this component")

parser = argparse.ArgumentParser('config.py',description="Script for setting up Crossbar configuration file")

parser.add_argument("--filename", default=config["CROSSBAR"]["configfile"], type=str, help="directory to place the generated configuration file")
parser.add_argument("--path", default=config["CROSSBAR"]["path"], type=str, help="directory to place the generated configuration file")

add_nlp = parser.add_argument_group('nlp', 'arguments for setting up NeuroNLP')
add_nlp.add_argument("--nlp-path", dest='nlp_path', default=config["NLP"]["path"], type=str, help="path to the NeuroNLP folder")
add_nlp.add_argument("--nlp-port", dest='nlp_port', default=int(config["NLP"]["port"]), type=int, help="port number for hosting NeuroNLP, default is 8081")


add_gfx = parser.add_argument_group('gfx', 'arguments for setting up NeuroGFX')
add_gfx.add_argument("--gfx-path", dest='gfx_path', default=config["GFX"]["path"], type=str, help="path to the NeuroGFX folder")
add_gfx.add_argument("--gfx-port", dest='gfx_port', default=int(config["GFX"]["port"]), type=int, help="port number for hosting NeuroGFX, default is 8082")

add_ssl = parser.add_argument_group('ssl', 'arguments for setting up ssl connection')
add_ssl.add_argument('--ssl', dest='ssl', action='store_true', help='enable ssl connection; ssl is disabled by default')
add_ssl.add_argument("--ssl-cert", dest='ssl_cert', default=config["AUTH"]["cert"], help="path to the certificate file")
add_ssl.add_argument("--ssl-key", dest='ssl_key', default=config["AUTH"]["key"], help="path to the key file")
add_ssl.add_argument("--chain-cert", dest='chain_cert', default=config["AUTH"]["chain-cert"], help="path to the chain certificate file")
parser.set_defaults(ssl=eval(config["AUTH"]["ssl"]))

add_sandbox = parser.add_argument_group('sandbox', 'arguments for setting up sandbox')
add_sandbox.add_argument('--no-sandbox', dest='sand_box', action='store_false', help='disable sandbox directory; sandbox is enabled by default')
add_sandbox.add_argument("--sandbox-path", dest='sandbox_path', default=config["SANDBOX"]["path"], type=str, help="path to the sandbox folder")
add_sandbox.add_argument("--sandbox-port", dest='sandbox_port', default=int(config["SANDBOX"]["port"]), type=int, help="port number for hosting sandbox, default is 8083")
parser.set_defaults(sandbox=eval(config["SANDBOX"]["sandbox"]))

args = parser.parse_args()

print("Generating Crossbar configuration file...")

# load default configuration
default_config = json.load(open(os.path.join(os.path.dirname(__file__),"components/.crossbar/default_config.json")));

# handle sandbox options
if args.sandbox:
    default_config["workers"][0]["transports"][2]["endpoint"]["port"] = args.sandbox_port
    default_config["workers"][0]["transports"][2]["paths"]["/"]["directory"] = args.sandbox_path
else:
    del default_config["workers"][0]["transports"][2]

# handle SSL options
if args.ssl:
    for i in xrange(len(default_config["workers"][0]["transports"])):
        default_config["workers"][0]["transports"][i]["endpoint"]["tls"]["certificate"] = args.ssl_cert
        default_config["workers"][0]["transports"][i]["endpoint"]["tls"]["key"] = args.ssl_key
        default_config["workers"][0]["transports"][i]["endpoint"]["tls"]["chain_certificates"][0] = args.chain_cert
else:
    for i in xrange(len(default_config["workers"][0]["transports"])):
        del default_config["workers"][0]["transports"][i]["endpoint"]["tls"]

# handle NLP options
default_config["workers"][0]["transports"][0]["endpoint"]["port"] = args.nlp_port
default_config["workers"][0]["transports"][0]["paths"]["/"]["directory"] = args.nlp_path

# handle GFX options
default_config["workers"][0]["transports"][1]["endpoint"]["port"] = args.gfx_port
default_config["workers"][0]["transports"][1]["paths"]["/"]["directory"] = args.gfx_path

# dump the reconfigured json
json.dump(default_config, open(os.path.join(args.path, args.filename), "w"),
    indent=4, separators=(',',':'))

print("The created file is stored at: " + os.path.join(args.path, args.filename))
