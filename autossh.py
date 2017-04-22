#!/usr/bin/env python3
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import time
import sys
import threading
from subprocess import Popen, PIPE, STDOUT
import traceback
import json
import argparse
import re
import datetime

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--config', default=sys.argv[0] + '.conf', help='config file location')
parser.add_argument('--ssh-user', help='ssh user for ssh connection')
parser.add_argument('--ssh-host', help='remote host for ssh connection')
parser.add_argument('--ssh-options', help='additional options for ssh, for example "-tt -o AddressFamily=inet -o ExitOnForwardFailure=yes"')
parser.add_argument('--ssh-forwards', help='forward options for ssh, for example "-R 2001:127.0.0.1:22"')
parser.add_argument('--ssh-key', help='private key for ssh connection, for example "/home/mu_user/.ssh/id_rsa_pf"')
parser.add_argument('--pid-file', help='pid file location')
parser.add_argument('--log-file', help='log file location')
parser.add_argument('--log-level', help='set output level for log messages')
parser.add_argument('--connection-tester-interval', type=int, help='interval for watchdog message check, will break connection if control message not received')
parser.add_argument('--disable-connection-tester', type=bool, help='disable connection testing via remote script if --disable-connection-tester="if_not_empty_string"')
parser.add_argument('--daemon', type=bool, help='enable daemon mode if --daemon="if_not_empty_string"')
args = parser.parse_args()

# init config dictionary
conf = dict()

# get config from json file
conf_file = json.load(open(args.config))

# add parsed from config_file to config dictionary
for key in conf_file:
    conf[key] = conf_file[key]

# add parsed args to config dictionary
for key in vars(args):
    if vars(args)[key]:
        conf[key] = vars(args)[key]
# make int for sure :)
conf['connection-tester-interval'] = int(conf['connection-tester-interval'])

# fork if daemon mode
if conf['daemon']:
    if os.fork():
        sys.exit()

# write pid file
with open(conf['pid-file'], 'w') as pid:
    pid.write(str(os.getpid()))

# open log file
log_file = open(conf['log-file'], 'w')

def do_log(message, level):
    '''
    Write logs to file or stdout - regarding to log level
    Can write to output via appropriate config option
    '''
    levels = ('debug', 'info', 'none')
    if conf['log-level'] == 'output':
        print(str(datetime.datetime.now()) + ' ' + str(message).strip())
        return
    if level == conf['log-level']:
        log_file.write(str(datetime.datetime.now()) + ' ' + str(message).strip() + '\n')
        log_file.flush()

def receive_stdout_message():
    '''
    Thread for receiving stdout messages from subprocess
    Will test message value if appropriate option is set
    Will add message to control set, which checked by watchdog 
    '''
    while data['alive']:
        if data.get('stdout'):
            message = data['stdout'].readline().decode('UTF-8')[:1]
            if not message:
                do_log('null stdout: ' + message, 'debug')
                time.sleep(1)
            # message validation if enabled
            if message == '1':
                continue
            if message != '2':
                data['alive'] = False
                do_log('Stdout message is not valid, stdout: ' + str(message), 'debug')
                continue
            data['message'].add(message)
            do_log('stdout: ' + message, 'debug')
        else:
            time.sleep(1)

def receive_stderr_message():
    '''Thread for receiving sterror messages from subprocess'''
    while data['alive']:
        if data.get('stderr'):
            message = data['stderr'].readline().decode('UTF-8')
            if not message:
                time.sleep(1)
                continue
            do_log('stderr: ' + str(message), 'debug')
        else:
            time.sleep(1)

def watchdog():
    '''Watchdog which check for new messages from stdout thread, if new mesage is not exists, then make signal for all threads stop'''
    while data['alive']:
        if data.get('stdout'):
            try:
                time.sleep(conf['connection-tester-interval'])
                continue
                message = data['message'].pop()
            except KeyError:
                data['alive'] = False
                do_log('No stdout, exit', 'debug')
        else:
            time.sleep(1)


# Add AddressFamily inet to sshd config, because it forward ip6 only if ipv4 failed and fucks everething
def ssh():
    '''
    Do ssh to destination host and controll threads count
    If threads count not have right value stop all threads and start from scratch
    Write controll messages for destination host
    '''
    template = 'ssh {0} -i {1} {2} {3}@{4}'
    command = template.format(conf['ssh-options'],
                              conf['ssh-key'], 
                              conf['ssh-forwards'],
                              conf['ssh-user'],
                              conf['ssh-host']).split()

    proc = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    # create data exchange points
    # stdout exchange point for stdout thread
    data['stdout'] = proc.stdout
    # stderr exchange point for stderr thread
    data['stderr'] = proc.stderr
    # exchange point for stdout and watchdog threads
    data['message'] = set()

    # write to stdin controll messages and signal to stop all threads if any thread is dead
    stdin_line = '1\n'
    while data['alive']:
        # if connection check is disabled then skip threading checks and stdin messages write
        if conf['disable-connection-tester']:
            message = data['stderr'].readline().decode('UTF-8')
            if not message:
                break
            do_log('stderr: ' + str(message), 'debug')
            continue
        else:
            proc.stdin.write(stdin_line.encode('UTF-8'))
            proc.stdin.flush()
        time.sleep(2)
        # make stop signal if not all thrads rinning
        if threading.active_count() != 4:
            data['alive'] = False
            do_log('Some thread is dead', 'debug')

# main loop, which always run fresh start after all threads exit
while True:
    try:
        # if connection check is disabled then do not start other threads
        if not conf['disable-connection-tester']:
            # loo which wait for all threads exit befoe fresh start
            while threading.active_count() != 1:
                do_log('Waiting for all threads stop Threads count: ' + str(threading.active_count()), 'debug')
                data['alive'] = False
                time.sleep(1)
            # fresh start begin
            data = dict()
            data['alive'] = True
            thread_stdout = threading.Thread(target=receive_stdout_message)
            thread_stdout.daemon = True
            thread_stdout.start()
            thread_stderr = threading.Thread(target=receive_stderr_message)
            thread_stderr.daemon = True
            thread_stderr.start()
            thread_watchdog = threading.Thread(target=watchdog)
            thread_watchdog.daemon = True
            thread_watchdog.start()
        else:
            data = dict()
            data['alive'] = True

        do_log('New iteration Threads count: ' + str(threading.active_count()), 'debug')
        do_log('Connection started', 'info')

        ssh()
    # stop if Ctrl + C
    except KeyboardInterrupt:
        sys.exit(0)
    # write all exceptions to log and keep going
    except:
        trace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        do_log(str(trace), 'info')
        time.sleep(1)
         
