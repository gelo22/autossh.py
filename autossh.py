#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import time
import sys
from subprocess import Popen, PIPE
import traceback
import json
import argparse
import datetime
import signal
import socket

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--config', default=sys.argv[0] + '.conf', help='config file location')
parser.add_argument('--ssh_user', help='ssh user for ssh connection')
parser.add_argument('--ssh_host', help='remote host for ssh connection')
parser.add_argument('--ssh_port', type=int, help='remote port for ssh connection')
parser.add_argument('--ssh_port_timeout', type=int, help='timeout in seconds for remote ssh port test')
parser.add_argument('--ssh_options', help='additional options for ssh, for example "-tt -o AddressFamily=inet -o ExitOnForwardFailure=yes"')
parser.add_argument('--ssh_forwards', help='forward options for ssh, for example "-R 2001:127.0.0.1:22"')
parser.add_argument('--ssh_key', help='private key for ssh connection, for example "/home/mu_user/.ssh/id_rsa_pf"')
parser.add_argument('--pid_file', help='pid file location')
parser.add_argument('--log_file', help='log file location')
parser.add_argument('--stdout_log_file', help='file for ssh process stdout')
parser.add_argument('--stderr_log_file', help='file for ssh process stderr')
parser.add_argument('--log_level', help='set output level for log messages (debug, info, none, stdout)')
parser.add_argument('--connection_tester_interval', type=int, help='interval for watchdog message check, will break connection if control message not received')
parser.add_argument('--disable-connection-tester', type=bool, help='disable connection testing via remote script if --disable-connection-tester="if_not_empty_string"')
parser.add_argument('--daemon', type=bool, help='enable daemon mode if --daemon="if_not_empty_string"')
args = parser.parse_args()

def parse_configuration():
    '''Parse configuration from config and cmd'''
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
    return conf

def pre_run_checks():
    '''Check mandatory things before start'''
    for key in conf:
        if key.find('file') != -1:
            file_name = conf[key]
            dir_name = os.path.dirname(file_name)
            if not os.path.isdir(dir_name):
                os.mkdir(dir_name, 0o750)
            try:
                with open(file_name, 'a') as write_check:
                    pass
            except IOError:
                conf['log_level'] = 'stdout'
                print('File {0} is not writable, will log to stdout'.format(file_name))
            
def fork():
    '''Fork process if daemon mode'''
    if conf['daemon']:
        if os.fork():
            sys.exit()

def write_pid():
    '''Write main process PID to file'''
    with open(conf['pid_file'], 'w') as pid:
        pid.write(str(os.getpid()))

def open_log():
    '''Open main log file'''
    if conf['log_level'] == 'stdout':
        log_file = sys.stdout
    else:
        log_file = open(conf['log_file'], 'w')
    return log_file

def do_log(message, level):
    '''
    Write logs to file or stdout - regarding to log level
    Can write to output via appropriate config option
    '''
    levels = { 'none': 0, 'info': 1, 'warn': 2, 'debug': 3 }
    current_time = datetime.datetime.now()
    if conf['log_level'] == 'stdout':
        message = '{0} {1}\n'.format(current_time, str(message).strip())
        log_file.write(message)
        log_file.flush()
   #    print(message, flush=True)
        return
    level_weight = levels[level]
    conf_level_weight = levels[conf['log_level']]
    if conf_level_weight >= level_weight:
        message = '{0} {1}: {2}\n'.format(datetime.datetime.now(), level.upper(), str(message).strip())
        log_file.write(message)
        log_file.flush()

def watchdog(proc):
    '''Watchdog which check for new messages from stdout thread, if new mesage is not exists, then make signal for all threads stop'''
    # write to stdin controll messages
    stdin_line = '1\n'
    stdout_counter = conf['connection_tester_interval']
    truncate_counter = conf['connection_tester_interval']
    if not conf['disable_connection_tester']:
        while stdout_counter > 0:
            proc.stdin.write(stdin_line.encode('UTF-8'))
            proc.stdin.flush()
            size_old = os.stat(conf['stdout_log_file']).st_size
            time.sleep(1)
            size_new = os.stat(conf['stdout_log_file']).st_size
            if size_new <= size_old:
                stdout_counter -= 1
            else:
                stdout_counter = conf['connection_tester_interval']
            truncate_counter -= 1
            if truncate_counter <= 0:
                truncate_counter = conf['connection_tester_interval']
                with open(conf['stdout_log_file'], 'w') as truncate_log:
                    pass
            if data['reload_daemon']:
                break
        pid = proc.pid
        os.kill(pid, 9)
    else:
        proc.wait()
                
# Add AddressFamily inet to sshd config, because it forward ip6 only if ipv4 failed and fucks everething
def ssh():
    '''
    Do ssh to destination host and controll threads count
    If threads count not have right value stop all threads and start from scratch
    Write controll messages for destination host
    '''
    template = 'ssh -p {0} -o ConnectTimeout={1} {2} -i {3} {4} {5}@{6}'
    command = template.format(conf['ssh_port'],
                              conf['ssh_port_timeout'],
                              conf['ssh_options'],
                              conf['ssh_key'], 
                              conf['ssh_forwards'],
                              conf['ssh_user'],
                              conf['ssh_host']).split()

    proc_stdout=open(conf['stdout_log_file'], 'w')
    proc_stderr=open(conf['stderr_log_file'], 'w')
    proc = Popen(command, stdin=PIPE, stdout=proc_stdout, stderr=proc_stderr)
    return proc

def set_reload_daemon(signum, frame):
    '''Set reload status to True'''
    data['reload_daemon'] = True

def set_exit_daemon(signum, frame):
    '''Set exit status to True'''
    sys.exit(0)

def is_ssh_port_open(host, port):
    '''Check if remote ssh port is open'''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(float(conf['ssh_port_timeout']))
        s.connect((host, port))
        resp = s.recv(100)
        s.close()
        return True
    except socket.error:
        return False
    except socket.timeout:
        return False

def read_ssh_log(stdout_log_file_name, stderr_log_file_name):
   #do_log(read_ssh_log(conf['stdout_log_file'], conf['stderr_log_file']), 'info')
   #read_ssh_log(conf['stdout_log_file'], conf['stderr_log_file'])
    message = ''
    if os.path.isfile(stdout_log_file_name):
        with open(stdout_log_file_name) as log_file:
            for line in log_file:
                if line not in ['1\n', '2\n']:
                    message += 'Ssh stdout log: {0}'.format(line)
        with open(stdout_log_file_name, 'w') as log_file:
            pass
    if os.path.isfile(stderr_log_file_name):
        with open(stderr_log_file_name) as log_file:
            for line in log_file:
                message += 'Ssh stderr log: {0}'.format(line)
        with open(stderr_log_file_name, 'w') as log_file:
            pass
    return message

if __name__ == '__main__':
    # first run things
    try:
        conf = parse_configuration()
        pre_run_checks()
        log_file = open_log()
        write_pid()
        fork()
        for key in conf:
            do_log('{0}: {1}'.format(key, conf[key]), 'debug')
    except:
        trace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        do_log(str(trace), 'info')
        time.sleep(conf['connection_tester_interval'])

    # main loop, which always run fresh start after all threads exit
    # add dictionary for data exchange
    data = { 'reload_daemon': False }
    # set reload signal and function for reload process
    signal.signal(signal.SIGHUP, set_reload_daemon)
    signal.signal(signal.SIGTERM, set_exit_daemon)
    while True:
        try:
            if data['reload_daemon']:
                data['reload_daemon'] = False
                do_log('Reloading daemon', 'info')
                conf = parse_configuration()
                pre_run_checks()
                log_file = open_log()
                for key in conf:
                    do_log('{0}: {1}'.format(key, conf[key]), 'debug')
            pre_run_checks()
            if not is_ssh_port_open(conf['ssh_host'], conf['ssh_port']):
                do_log('remote ssh port is not accessible, sleeping', 'info')
                time.sleep(conf['connection_tester_interval'])
                continue
            do_log(read_ssh_log(conf['stdout_log_file'], conf['stderr_log_file']), 'info')
            do_log('New connection started', 'info')
            proc = ssh()
            watchdog(proc)

        # stop if Ctrl + C
        except KeyboardInterrupt:
            sys.exit(0)
        except SystemExit:
            sys.exit(0)
        # write all exceptions to log and keep going
        except:
            trace = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            do_log(str(trace), 'info')
            time.sleep(conf['connection_tester_interval'])
