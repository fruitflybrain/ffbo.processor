from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList
from twisted.logger import Logger

from twisted.internet import task, threads, reactor

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession,  ApplicationRunner
from autobahn.wamp.exception import ApplicationError
from autobahn.wamp.types import RegisterOptions

import smtplib
from email.mime.text import MIMEText

import os

from tinydb import TinyDB, where, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

import random
import string

import autobahn.wamp.auth as ath

import copy

import six

class AppSession(ApplicationSession):

    log = Logger()


    @inlineCallbacks
    def onJoin(self, details):

        middleware = CachingMiddleware(JSONStorage)
        db = TinyDB(os.path.join(os.path.dirname(__file__),'data','user_data.json'),
                          storage=middleware)
        auth_config = {'salt': 'fruitfly', 'iterations':5000,'keylen':32}
        session_user_map = {}
        chars = string.ascii_letters + string.digits + "@!^_()%[]{}"
        pwlen = 12

        self.log.info('auth started')

        def auth(realm, authid, details):
            q = Query()
            results = db.search(q.username == authid)
            if not results:
                raise ApplicationError("User does not exist", "could not authenticate session - no such user {}".format(authid))
            auth_details = results[0]['auth_details']
            auth_details['authid'] = results[0]['user_details']['fname']
            if results[0]['user_details']['lname']:
                auth_details['authid'] += (" " + results[0]['user_details']['lname'])
            if not auth_details['authid']: del auth_details['authid']
            session_user_map[details['session']]={'username': authid, 'details':details}
            return auth_details


        yield self.register(auth, six.u('ffbo.auth_server.auth'))
        self.log.info("registered ffbo.auth_server.auth")

        def get_user(session):
            if session in session_user_map:
                return session_user_map[session]
            return {}

        yield self.register(get_user, six.u('ffbo.auth_server.get_user'))
        self.log.info("registered ffbo.auth_server.get_user")

        def generate_password():
            rnd = random.SystemRandom()
            return "".join([rnd.choice(chars) for _ in range(pwlen)])

        def register_user(user_details):
            if user_exists(user_details['username']):
                return {"error": "User already exists. Please try again"}
            try:
                username = user_details['username']
                pw = generate_password()
                salted_pw = ath.derive_key(pw,
                                           auth_config['salt'],
                                           auth_config['iterations'],
                                           auth_config['keylen'])
                db_rec = {'username':username,
                          'user_details': user_details,
                          'auth_details': copy.deepcopy(auth_config)}
                db_rec['auth_details']['secret'] = salted_pw
                db_rec['auth_details']['role'] = u'user'
                del db_rec['user_details']['username']
                #print "Registered user ",  db_rec
                db.insert(db_rec)
            except Exception as e:
                print e
                return {"error": "Unexpected error occured. Please try again"}
            print "User added to database"
            send_email(user_details, pw, username)
            return {"success": "Successfuly registered. Please check your email for your password."}

        yield self.register(register_user, six.u('ffbo.auth_server.register_user'))
        self.log.info("registered ffbo.auth_server.register_user")

        def send_email(user_details, pw, username):
            title = "Thank you for registering at NeuroNLP"
            text = "Hi {fname},\n\n"
            text += "Here are your login details for NeuroNLP.\n\n"
            text += "Username: {username}\nPassword: {pw}\n\n"
            text += "If you have any suggestions or feedback, we would love to hear it!"
            text += " Please use the feedback button on the top left button of the website to write to us.\n\n"
            text += "Thank you,\nFruit Fly Brain Observatory"
            text = text.format(username=username,fname=user_details['fname'], pw=pw)

            msg = MIMEText(text)

            msg['Subject'] = title
            msg['From'] = 'NeuroNLP(Fruit Fly Brain Observatory) <no-reply@fruitflybrain.org>'
            msg['To'] = user_details['email']
            sender = msg['From']

            try:
                s = smtplib.SMTP(host='localhost', port=465)
            except Exception as e:
                print e
                print "Failed to start SMTP server on localhost"
            try:
                # Use a valid smtp server, otherwise the email notification won't be sent out
                s.sendmail('no-reply@fruitflybrain.org', [user_details['email']], msg.as_string())
                middleware.flush()
                print "Email sent to " + user_details['email'] + " for " + user_details['fname'] + ' ' + user_details['lname']
            except Exception as e:
                print e
                print "Failed to send out email"


        def user_exists(username):
            q = Query()
            results = db.search(q.username == username)
            if not results:
                return False
            return True

        yield self.register(user_exists, six.u('ffbo.auth_server.user_exists'))
        self.log.info("registered ffbo.auth_server.user_exists")

        def get_auth_config():
            return auth_config

        yield self.register(get_auth_config, six.u('ffbo.auth_server.get_auth_config'))
        self.log.info("registered ffbo.auth_server.get_auth_config")

        def change_password():
            pass

        def send_new_password():
            pass
