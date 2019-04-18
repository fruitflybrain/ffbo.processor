from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList, Deferred
from twisted.logger import jsonFileLogObserver, Logger

from twisted.internet import task, threads, reactor

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession,  ApplicationRunner
from autobahn.wamp.exception import ApplicationError
from autobahn.wamp.types import RegisterOptions

import smtplib
from email.mime.text import MIMEText

import json
import os
import io
import argparse
import six
import socket
import txaio

import pandas as pd

import pdb

import copy

from autobahn.wamp.types import CallOptions

from crawl import FlyCircuitDB

import traceback

class AppSession(ApplicationSession):

    fdb = FlyCircuitDB()
    log = Logger()
    txaio.start_logging(level='debug')
    feedback_log = Logger(
        observer=jsonFileLogObserver(
            io.open(
                os.path.join(
                    os.path.dirname(__file__),'logs','feedback_log.json'), 'a+b')), namespace='feedback')
    #log = Logger(observer=jsonFileLogObserver(io.open("processor_log.json", "a")), namespace="saver")

    @inlineCallbacks
    def onJoin(self, details):

        # Processor Data
        directory = {
            'nlp':{},
            'na' :{},
            'nk': {}
        }

        # Email notification
        # email_dict = {
        #    "sender": "me@email.com",
        #    "recipients": {"John Doe": "joe@email.com",
        #                   "Jane Who": "jane@email.com"
        #    }
        # }
        email_dict = None
        try:
            with open('email_dict.json') as data_file:
                email_dict = json.load(data_file)
                self.log.info("Loading Email Dictionary with keys, {keys}",keys=email_dict.keys())
        except:
            self.log.warn("Loading Email Dictionary failed, no email notification on session leave.")

        # Memory Management
        @inlineCallbacks
        def trigger_memory_management():
            yield self.publish(six.u('ffbo.processor.memory_manager'))
            self.log.info('Memory Management ping: ffbo.processor.memory_manager')


        lc = task.LoopingCall(trigger_memory_management)
        interval = 60*30 # 30 mins
        lc.start(interval)

        def get_process_info():
            # hacky way to determine whether process is inside docker
            try:
                cgroup = {}
                with open('/proc/1/cgroup') as f:
                    for line in f:
                        field = line.split(':')
                        if len(field) == 3:
                            cgroup[field[1]] = field[2]
                docker_cid = 'not inside docker'
                if cgroup.has_key('cpu'):
                    field = cgroup['cpu'].strip().split('/')
                    if len(field) > 2 and field[1] == 'docker':
                        docker_cid = field[2]
            except:
                docker_cid = 'cat not determine whether inside docker or not'

            # get process pid
            try:
                pid = os.getpid()
            except:
                pid = None

            # get host IP, messy code for cross platform support
            try:
                hostip = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1]
                hostip = hostip or [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]
                hostip = hostip[0]
            except:
                hostip = None

            process_info = "\n\n" \
                           "processor_component pid: {pid}\n" \
                           "docker container id: {cid}\n" \
                           "host ip address: {hip}\n".format(pid=str(pid),cid=str(docker_cid),hip=str(hostip))
            return process_info


        def send_email(text, subject=None, verbose=True):
            try:
                sender = email_dict['sender']
                recipients = ['%s <%s>' % (k,v) for k,v in email_dict['recipients'].items()]
            except:
                return "Incorrect email dictionary format"

            if verbose:
                text += get_process_info()

            msg = MIMEText(text)

            msg['Subject'] = '[FFBO Server] ' + subject
            msg['From'] = sender
            msg['To'] = ','.join(recipients)

            gmail_user = ""
            gmail_pwd = ""

            try:
                s = smtplib.SMTP_SSL("smtp.gmail.com",465)
                s.login(gmail_user, gmail_pwd)
            except Exception as e:
                print e
                return "Failed to connect to SMTP server on gmail"
            try:
                s.sendmail(sender, recipients, msg.as_string())
            except:
                return "Failed to send out email"
            s.quit()
            return "successfully sent out email"


        def feedback_error(request,message,exception=None):
            info =  {'error':
                        {'request': str(request),
                         'message':str(message),
                         'exception':str(exception)
                        }
                    }
            return info

        def feedback_success(request,result):
            info = {'success':
                    {'request': str(request),
                     'result': result,
                    }
                }
            return info

        @inlineCallbacks # Progressive calls
        def process_nlp_query(request,details=None):
            """
                Process a nlp request, this request should have
                user:       session_id
                servers: {  nlp: session_id,
                            na : session_id,
                            vis: session_id
                         }
                nlp_query:  string
            """
            request['user'] = details.caller
            #user_details = yield self.call('ffbo.auth_server.get_user',details.caller)
            user_details = yield self.call(six.u('ffbo.auth_server.get_user'),details.caller)
            if user_details: request['username'] = user_details['username']
            feedback = []
            self.log.info("process_nlp_query() accessed with request: {request}", request=request)
            # Validate 3 each server is defined
            try:
                #build up server calls
                rpc_calls = {}
                for stype in ['nlp', 'na']:
                    rpc_calls[stype] = six.u("ffbo.%(s_type)s.query.%(s_id)s" % \
                    {'s_id':    request['servers'][stype],
                     's_type':  stype})
                rpc_calls['user_msg'] = six.u("ffbo.ui.receive_msg.%(s_id)s" % \
                                        {'s_id': request['user']})
            except Exception as e:
                self.log.warn("process_nlp_query() failed due to incomplete server list in {servers}", servers= str(request['servers']))
                feedback =  feedback_error(request,"Server list not fully defined",e)
                returnValue(feedback)


            # Natural Language Processing
            try:
                self.log.info("process_nlp_query() accessed on NLP server {server_id} with query: {query}",
                                      server_id=rpc_calls['nlp'],query=request['nlp_query'])

                language = "en"
                if "language" in request:
                    language = request["language"]

                nlp_res =  yield self.call(rpc_calls['nlp'], request['nlp_query'],language)
                self.log.info("process_nlp_query() accessed on NLP server {server_id} with result: {result}",
                          server_id=rpc_calls['nlp'],result=nlp_res)

            except ApplicationError as e:
                self.log.warn("Processor failed to access NLP server {server_id}, with error {e}",
                              server_id=rpc_calls['nlp'],e=e)

                feedback = feedback_error(request,"Unable to contact server",e)
                returnValue(feedback)

            try:
                if nlp_res == {}:
                    yield self.call(rpc_calls['user_msg'], {'info':{'error':
                                                'NLP module could not parse your input'}})
                    self.log.warn("{server_id} failed to parse query: {query}}",
                                  server_id=rpc_calls['nlp'],query=request['nlp_query'])
                    returnValue(None)
                yield self.call(rpc_calls['user_msg'], {'info':{'success':
                                    'NLP module successfully parsed your input'}})
                nlp_res['user_msg'] = rpc_calls['user_msg']
                for key in request:
                    if key not in nlp_res: nlp_res[key]=request[key]

                nlp_res['user'] = request['user']
                # HARD CODE morphology if not specified
                nlp_res['format'] = 'morphology' if not 'format' in request \
                                    else request['format']

                if 'verb' not in nlp_res or nlp_res['verb'] == 'show':
                    yield self.call(rpc_calls['user_msg'],
                                    {'commands': {'reset':''}})

                na_res = yield self.call(rpc_calls['na'], nlp_res)
                if not na_res:
                    yield self.call(rpc_calls['user_msg'], {'info':{'error':
                                        'Failed to execute query on Neuroarch'}})
                    returnValue(None)
                else:
                    if not 'format' in request: request['format'] = 'morphology'
                    msg = {'info':{'success':'Finished fetching all results from NeuroArch'}}
                    self.call(rpc_calls['user_msg'], msg)
                    returnValue(na_res)
            except ApplicationError as e:
                self.log.warn("Processor failed to access NA server {server_id}, with error {e}",
                              server_id=rpc_calls['na'],e=e)
                traceback.print_exc()
                yield self.call(rpc_calls['user_msg'], {'info':{'error':
                                        'Unable to contact NeuroArch server'}})
                returnValue(None)

        yield self.register(process_nlp_query, six.u('ffbo.processor.nlp_to_visualise'), RegisterOptions(details_arg='details'))
        self.log.debug("procedure process_nlp_query registered")


        @inlineCallbacks # Progressive calls
        def process_nk_request(request,details=None):
            """

            """
            request['user'] = details.caller
            user_details = yield self.call(six.u('ffbo.auth_server.get_user'),details.caller)
            if user_details: request['username'] = user_details['username']
            feedback = []
            self.log.debug("process_nk_request() accessed with request: {request}", request=request)
            # Validate 3 each server is defined
            try:
                #build up server calls
                rpc_calls = {}
                rpc_calls['na'] = u'ffbo.na.query.' + request['servers']['na']
                rpc_calls['nk'] = u'ffbo.nk.launch.' + request['servers']['nk']

            except Exception as e:
                self.log.warn("process_nk_request() failed due to incomplete server list in {servers}", servers= str(request['servers']))
                feedback =  feedback_error(request,"Server list not fully defined",e)
                returnValue(feedback)


            # Natural Language Processing
            na_res = request
            try:
                na_task = {'user': request['user'],
                           'command': {"retrieve":{"state":0}},
                           'format': "nk"}
                self.log.info("process_nk_request() accessed on NA server {server_id} with query: {query}",
                                      server_id=rpc_calls['na'], query=na_task)

                #na_res =  yield self.call(rpc_calls['na'], na_task)
                na_res_update =  yield self.call(rpc_calls['na'], na_task)
                na_res.update(na_res_update)
                self.log.info("process_nk_request() accessed on NA server {server_id} with result: {result}",
                              server_id=rpc_calls['na'],result=na_res)

            except ApplicationError as e:
                self.log.warn("Processor failed to access NLP server {server_id}, with error {e}",
                              server_id=rpc_calls['nlp'],e=e)

                feedback = feedback_error(request,"Unable to contact server",e)
                returnValue(feedback)

            details.progress("Circuit data retrieved from NeuroArch")

            try:
                na_res['user'] = request['user']
                if 'neuron_list' in request:
                    na_res['neuron_list'] = request['neuron_list']

                progressive_result = {}
                def on_progress(p):
                    progressive_result.update(p)
                    details.progress("Receive partial result from execution.")

                details.progress("Start execution in Neurokernel")
                # Fprward result to the Front End
                na_res["forward"] = six.u("ffbo.gfx.receive_partial." + str(na_res['user']))
                nk_res =  yield self.call(rpc_calls['nk'], na_res, options=CallOptions(on_progress=on_progress, timeout = 30000000000))

                # Did we use a progressive result
                if nk_res is None:
                    nk_res = progressive_result

                if nk_res == {}:
                    feedback =feedback_error(request,"Neurokernel returned zero results")
                    returnValue(feedback)
                #details.progress("Circuit execution completed")

            except ValueError as e:
                self.log.warn("{server_id} failed to start simulation: {query}}",
                                      server_id=rpc_calls['nk'], query=na_res)
                feedback = feedback_error(request,"Execution Failure",e)
                returnValue(feedback)

            except ApplicationError as e:
                self.log.warn("Processor failed to access NK server {server_id}, with error {e}",
                    server_id=rpc_calls['nk'],e=e)

                feedback =feedback_error(request,"Execution Failure",e)
                returnValue(feedback)

            #details.progress("Neurokernel Started Execution")

            try:
                vis_res = {
                    'success': {'result':{
                        'user'          : request['user'],
                        'type'          : 'json'
                        },
                    'user': request['user'],
                    'reset'         : False
                    }
                }

                if 'error' in vis_res:
                    raise RuntimeError('Visualisation component was unable to complete the request ')

            except Exception as e:
                self.log.warn("Processor failed to access complete visualisation")
                feedback = feedback_error(request,"Unable to create on visualiser",e)
                returnValue(feedback)

            #details.progress("Visualisation: Parsed result")

            self.log.debug("Process_NK_Request complete with request: {request} and result: {result}",
                           request=request,result=vis_res)

            returnValue(vis_res)


        yield self.register(process_nk_request, six.u('ffbo.processor.nk_execute'), RegisterOptions(details_arg='details'))
        self.log.debug("procedure process_nk_request registered")


        # Recieve Feedback from the User
        @inlineCallbacks
        def log_feedback(user, feedback_message,details):
            try:
                user_details = yield self.call(six.u('ffbo.auth_server.get_user'),details.caller)
                template = "-"*70 + "Feedback recieved\n username: {user} \n feedback_message: {feedback}\n"
                yield self.feedback_log.info(template.format(user=user_details['username'],
                                                             feedback=feedback_message))
            except Exception as e:
                print e
                self.log.warn("Failed to log user feedback: {user} {feedback}",
                            user=user,
                            feedback=feedback_message)

                returnValue(False)
            returnValue(True)

        yield self.register(log_feedback, six.u('ffbo.server.log_feedback'),RegisterOptions(details_arg='details'))
        self.log.debug("registered ffbo.server.log_feedback")


        # SUBSCRIBE to session leaving events to check if a server needs removing
        @inlineCallbacks
        def on_session_leave(session_id):
            self.log.info("event for 'on_session_leave' received for session: " \
                    "{session}", session=session_id)
            for stype in directory.keys():
                if session_id in directory[stype].keys():
                    self.log.info("Server disconnected. removing session" \
                            "{session} of type {stype}", session=session_id, stype=stype)
                    if email_dict is not None:
                         email_res = None
                         title = "Server down"
                         text = "disconnected session {session} of type {stype}".format(
                             session=session_id, stype=stype)
                         self.log.info("Sending email about disconnected session" \
                             "{session} of type {stype}",
                             session=session_id,
                             stype=stype)
                         try:
                             email_res = send_email(text, title)
                         except Exception as e:
                             self.log.info("Sending email failed with error {error}",error=str(e))
                         if email_res is not None:
                             self.log.info("Tried to send out email... {msg}", msg=email_res)
                    del directory[stype][session_id]
                    yield self.publish(six.u('ffbo.server.update'), directory)

        yield self.subscribe(on_session_leave, six.u('wamp.session.on_leave'))
        self.log.debug("subscribed to topic 'wamp.session.on_leave'")



        # REGISTER a procedure for registering a new server
        @inlineCallbacks
        def register_new_server(server_id,server_type,server_name):
            if(not server_type in directory.keys()): returnValue({})
            self.log.info("{server_type} server registered with name " \
                            "{server_name} and id {server_id}",
                            server_name=server_name, server_id=server_id, \
                            server_type=server_type)

            directory[server_type][server_id] = {'name':server_name}

            # PUBLISH updated server list after a new server registration
            yield self.publish(six.u('ffbo.server.update'), directory)
            returnValue(json.dumps({'server':directory}))

        yield self.register(register_new_server, six.u('ffbo.server.register'))
        self.log.debug("procedure register_new_server registered")


        @inlineCallbacks
        def nlp_query(server_id,query,user=None):
            """
            Call the nlp module for a nlp translation
            Input

                rpc_call: the WAMP registered RPC call
                query   : the natural language to translate
                user    : used to record state, can be None for stateless

            Return:
                A success or error dictionary
            """

            try:
                self.log.info("nlp_query() accessed on NLP server {server_id} with query: {query}",
                                      server_id=server_id,query=query)
                nlp_res =  yield self.call("ffbo.nlp.query."+  str(server_id), query)
                self.log.info("nlp_query() accessed on NLP server {server_id} with result: {result}",
                                      server_id=server_id,result=nlp_res)

                # First Exit Point: NLP parsing has failed
                if nlp_res == {}:
                    raise ValueError('NLP parsing could not parse string')

                returnValue(feedback_success(query,nlp_res))

            except ApplicationError as e:
                # ignore errors due to the frontend not yet having
                # registered the procedure we would like to call
                raise e
                self.log.warn("nlp_query() failed to access NLP server {server_id}, with error {e}",
                    e=e)

                feedback = feedback_error(rpc_call,"Unable to contact server",e)
                returnValue(feedback)
            except ValueError as e:
                self.log.warn("nlp_query() accessed on {server_id} failed to parse query: {query}}",
                                  query=query)
                feedback = feedback_error(query,"NLP parsing could not parse string",e)
                returnValue(feedback)

        yield self.register(nlp_query, six.u('ffbo.processor.nlp_query'))
        self.log.debug("procedure ffbo.processor.nlp_query registered")


        @inlineCallbacks
        def neuroarch_query(request, details=None):
            """
            Call the neuroarch_query module with a neuroarch-json object
            The request should have
                user:       session_id for client
                server:     session_id for na server
                query:  neuroarch json query object
            """
            try:
                request['user'] = details.caller
                user_details = yield self.call(six.u('ffbo.auth_server.get_user'),details.caller)
                if user_details: request['username'] = user_details['username']
                self.log.info("neuroarch_query() accessed with request: {request}", request=request)

                progressive_result = {}
                def on_progress(p):
                    progressive_result.update(p)

                #print request
                result =  yield self.call(six.u('ffbo.na.query.'+str(request['server'])), request, options=CallOptions(on_progress=on_progress))
                self.log.info("na_query returned with result")

                if progressive_result:
                    result = progressive_result

                # Catch no results and return
                if result == "{}":
                    raise ValueError('Neuroarch returned zero results')
                returnValue(feedback_success(request,(result)))

            except ValueError as e:
                feedback = feedback_error(request,"Neuroarch returned zero results",e)
                returnValue(feedback)

            except ApplicationError as e:
                raise e
                feedback =feedback_error(server_id,"Unable to contact server",e)
                returnValue(feedback)


        yield self.register(neuroarch_query, six.u('ffbo.processor.neuroarch_query'), RegisterOptions(details_arg='details'))
        self.log.info("procedure ffbo.processor.neuroarch_query registered")

        @inlineCallbacks
        def flycircuit_neuron_query(neuron, details=None):
            self.log.info("Fetch the flycircuit database for neuron: {neuron}", neuron=neuron)
            try:
                res = self.fdb.parse_neuron(neuron)
            except Exception as e:
                print e
                res = feedback_error(neuron,"Unable to fetch flycircuit database",e)
                yield res
            returnValue(res)

        yield self.register(flycircuit_neuron_query, six.u("ffbo.processor.fetch_flycircuit"), RegisterOptions(details_arg='details',concurrency=4))
        self.log.info("procedure ffbo.processor.fetch_flycircuit registered")


        @inlineCallbacks
        def neurokernel_query(request):
            """
            Call the neuroarch_query module with a neuroarch-json object
            The request should have
                user:       session_id for client
                server:     session_id for na server
                query:  neuroarch json query object
            """
            try:
                progressive_result = {}
                def on_progress(p):
                    progressive_result.update(p)

                result =  yield self.call(six.u('ffbo.nk.launch.'+str(request['server'])), request)
                self.log.info("nk_query returned with result")

                if result is None:
                    result = progressive_result

                # Catch no results and return
                if result == "{}":
                    raise ValueError('Neurokernel returned zero results')
                returnValue(feedback_success(request,(result)))

            except ValueError as e:
                feedback = feedback_error(request,"Neurokernel returned zero results",e)
                returnValue(feedback)

            except ApplicationError as e:
                raise e
                feedback =feedback_error(server_id,"Unable to contact server",e)
                returnValue(feedback)


        # REGISTER a procedure for relaying current servers to single ui
        def relay_server_information():
            self.log.debug("relay_server_information rpc called")
            return directory

        yield self.register(relay_server_information, six.u('ffbo.processor.server_information'))
        self.log.debug("ffbo.processor.server_information registered")
        # Alert components to server registration
        #yield self.publish('ffbo.processor.connected')
        #self.log.debug("publish processor connected to ffbo.processor.connected")


if __name__ == '__main__':

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

    # Crossbar.io connection configuration
    url = "ws://crossbar:8080/ws"
    realm = config["SERVER"]["realm"]

    # parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output.')
    parser.add_argument('--url', dest='url', type=six.text_type, default=url, help='The router URL (default: "ws://localhost:8080/ws").')
    parser.add_argument('--realm', dest='realm', type=six.text_type, default=realm, help='The realm to join (default: "realm1").')

    args = parser.parse_args()

    # start logging
    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    # now actually run a WAMP client using our session class ClientSession
    runner = ApplicationRunner(url=args.url, realm=args.realm)
    runner.run(AppSession)
