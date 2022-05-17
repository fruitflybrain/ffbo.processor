import os,sys
import argparse
import simplejson as json

from configparser import ConfigParser
import requests
from requests.exceptions import Timeout
from autobahn.wamp.auth import derive_key

# Grab configuration from file
root = os.path.expanduser("/")
home = os.path.expanduser("~")
filepath = os.path.dirname(os.path.abspath(__file__))
config_files = []
config_files.append(os.path.join(home, ".ffbo/config", "ffbo.processor.ini"))
config_files.append(os.path.join(root, ".ffbo/config", "ffbo.processor.ini"))
config_files.append(os.path.join(home, ".ffbo/config", "config.ini"))
config_files.append(os.path.join(root, ".ffbo/config", "config.ini"))
config_files.append(os.path.join(filepath, "config.ini"))
config = ConfigParser()
configured = False
file_type = 0
for config_file in config_files:
    if os.path.exists(config_file):
        config.read(config_file)
        configured = True
        break
    file_type += 1
if not configured:
    raise Exception("No config file exists for this component")

# Create proper address to serve content from based on config file
ssl = eval(config["AUTH"]["ssl"])
websockets = "wss" if ssl else "ws"
if "ip" in config["SERVER"]:
    ip = config["SERVER"]["ip"]
else:
    # try:
    #     # first try to get public IP from aws to see if it is an aws ec2 instance.
    #     res = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout = 1.0)
    #     ip = res.text
    # except Timeout:
    ip = "localhost"
port = int(config["NLP"]["expose-port"])
processor_url = "%(ws)s://%(ip)s:%(port)s/ws" % {"ws":websockets, "ip":ip, "port":port}

guest_user = config['GUEST']['user']
guest_salt = config['GUEST']['salt']
guest_secret = config['GUEST']['secret']

# Replace proper address into js file
if os.path.isabs(config["NLP"]["path"]):
    jsfilename = os.path.join(config["NLP"]["path"], "config/config.json")
else:
    jsfilename = os.path.join(filepath, 'components/.crossbar', config["NLP"]["path"], "config/config.json")
with open(jsfilename, "r") as f:
    nlp_config = json.load(f)
nlp_config["connection"]["url"] = processor_url
nlp_config["connection"]["user"] = guest_user
nlp_config["connection"]["secret"] = guest_secret

with open(jsfilename, "w") as f:
    json.dump(nlp_config, f, indent=2 * ' ', separators=(',',':'))

# Replace user_data.json
with open(os.path.join(filepath, "components/processor_component/data/user_data.json"), "r") as f:
    userdata = json.load(f)
username = config["USER"]["user"]
salt = config["USER"]["salt"]
secret = derive_key(secret = config["USER"]["secret"], salt = config["USER"]["salt"], iterations = userdata["_default"]["1"]["auth_details"]["iterations"], keylen = userdata["_default"]["1"]["auth_details"]["keylen"])

userdata["_default"]["1"]["auth_details"]["secret"] = secret
userdata["_default"]["1"]["auth_details"]["salt"] = salt
userdata["_default"]["1"]["username"] = username

secret = derive_key(secret = guest_secret, salt = guest_salt, iterations = userdata["_default"]["2"]["auth_details"]["iterations"], keylen = userdata["_default"]["2"]["auth_details"]["keylen"])
userdata["_default"]["2"]["auth_details"]["secret"] = secret
userdata["_default"]["2"]["auth_details"]["salt"] = guest_salt
userdata["_default"]["2"]["username"] = guest_user

with open(os.path.join(filepath, "components/processor_component/data/user_data.json"), "w") as f:
    json.dump(userdata, f, indent=4 * ' ', separators=(',',':'))

parser = argparse.ArgumentParser('config.py',description="Script for setting up Crossbar configuration file")

parser.add_argument("--filename", default=config["CROSSBAR"]["configfile"], type=str, help="directory to place the generated configuration file")
parser.add_argument("--path", default=config["CROSSBAR"]["path"], type=str, help="directory to place the generated configuration file")

add_nlp = parser.add_argument_group('nlp', 'arguments for setting up NeuroNLP')
add_nlp.add_argument("--nlp-path", dest='nlp_path', default=config["NLP"]["path"], type=str, help="path to the NeuroNLP folder")
add_nlp.add_argument("--nlp-port", dest='nlp_port', default=int(config["NLP"]["port"]), type=int, help="port number for hosting NeuroNLP, default is 8081")

if "GFX" in config:
    add_gfx = parser.add_argument_group('gfx', 'arguments for setting up NeuroGFX')
    add_gfx.add_argument("--gfx-path", dest='gfx_path', default=config["GFX"]["path"], type=str, help="path to the NeuroGFX folder")
    add_gfx.add_argument("--gfx-port", dest='gfx_port', default=int(config["GFX"]["port"]), type=int, help="port number for hosting NeuroGFX, default is 8082")
    
add_ssl = parser.add_argument_group('ssl', 'arguments for setting up ssl connection')
add_ssl.add_argument('--ssl', dest='ssl', action='store_true', help='enable ssl connection; ssl is disabled by default')
add_ssl.add_argument("--ssl-cert", dest='ssl_cert', default=config["AUTH"]["cert"], help="path to the certificate file")
add_ssl.add_argument("--ssl-key", dest='ssl_key', default=config["AUTH"]["key"], help="path to the key file")
add_ssl.add_argument("--chain-cert", dest='chain_cert', default=config["AUTH"]["chain-cert"], help="path to the chain certificate file")
parser.set_defaults(ssl=eval(config["AUTH"]["ssl"]))

if "SANDBOX" in config:
    add_sandbox = parser.add_argument_group('sandbox', 'arguments for setting up sandbox')
    add_sandbox.add_argument('--no-sandbox', dest='sand_box', action='store_false', help='disable sandbox directory; sandbox is enabled by default')
    add_sandbox.add_argument("--sandbox-path", dest='sandbox_path', default=config["SANDBOX"]["path"], type=str, help="path to the sandbox folder")
    add_sandbox.add_argument("--sandbox-port", dest='sandbox_port', default=int(config["SANDBOX"]["port"]), type=int, help="port number for hosting sandbox, default is 8083")
    parser.set_defaults(sandbox=eval(config["SANDBOX"]["sandbox"]))

args = parser.parse_args()

print("Generating Crossbar configuration file...")

# load default configuration
default_config = json.load(open(os.path.join(filepath, "components/.crossbar/default_config.json")));

# handle sandbox options
if "SANDBOX" in config:
    default_config["workers"][0]["transports"][2]["endpoint"]["port"] = args.sandbox_port
    default_config["workers"][0]["transports"][2]["paths"]["/"]["directory"] = args.sandbox_path
else:
    del default_config["workers"][0]["transports"][2]

# handle SSL options
if args.ssl:
    for i in range(len(default_config["workers"][0]["transports"])):
        default_config["workers"][0]["transports"][i]["endpoint"]["tls"]["certificate"] = args.ssl_cert
        default_config["workers"][0]["transports"][i]["endpoint"]["tls"]["key"] = args.ssl_key
        default_config["workers"][0]["transports"][i]["endpoint"]["tls"]["chain_certificates"][0] = args.chain_cert
else:
    for i in range(len(default_config["workers"][0]["transports"])):
        del default_config["workers"][0]["transports"][i]["endpoint"]["tls"]

# handle NLP options
default_config["workers"][0]["transports"][0]["endpoint"]["port"] = args.nlp_port
default_config["workers"][0]["transports"][0]["paths"]["/"]["directory"] = args.nlp_path

# handle GFX options
if "GFX" in config:
    default_config["workers"][0]["transports"][1]["endpoint"]["port"] = args.gfx_port
    default_config["workers"][0]["transports"][1]["paths"]["/"]["directory"] = args.gfx_path
else:
    del default_config["workers"][0]["transports"][1]
# dump the reconfigured json
json.dump(default_config, open(os.path.join(args.path, args.filename), "w"),
    indent=4, separators=(',',':'))

print("The created file is stored at: " + os.path.join(args.path, args.filename))
