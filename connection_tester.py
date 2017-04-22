#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import time
import threading
import sys
import datetime
import argparse
import json

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--config', default=sys.argv[0] + '.conf', help='config file location')
parser.add_argument('--absent-messages-limit', type=int, help='set number of lost messages for autodestroy RESULT = absent_messages_limit * response_interval')
parser.add_argument('--response-interval', type=int, help='set response interval in seconds which this script will do before message write for remote host')
parser.add_argument('--log-file', help='log file location')
parser.add_argument('--hostname', help='client`s hostname')
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

# storage for messages
message_buffer = set()

# log file location
log = open('./connection_tester.py.log', 'w')

def receive_message():
    '''Thread which will read stdin for messages from remote host and add it to the storage'''
    message = 1
    while message:
        message = sys.stdin.readline()[:1]
        if message != '1':
            sys.exit(1)
        message_buffer.add(message)

# Thread start
thread = threading.Thread(target=receive_message)
thread.daemon = True
thread.start()

log.write(str(datetime.datetime.now()) + ' ' + 'start new tester' + '\n')
log.flush()
# Main loop, read message from storage, validate it, count broken messages and exit if limit exceeded and print output for remote server
# init counter
absent_messages_counter = 0
while True:
    print('2')
    time.sleep(conf['response-interval'])
    message = 0
    # exit if limit of lost remote messages exceeded
    if absent_messages_counter >= conf['absent-messages-limit']:
        sys.exit(0)
    try:
        # message read
        message = message_buffer.pop()
        # message validation
        if message == '1':
            absent_messages_counter = 0
        else:
            absent_messages_counter += 1
    except KeyError:
        absent_messages_counter += 1

