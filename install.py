#!/usr/bin/env python

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals

import shutil
import os
import argparse
from subprocess import Popen, PIPE
import pwd
#import bytes

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--host', default='notexist.zero', help='destination hostname for ssh connection')
parser.add_argument('--user', default='autossh_py', help='system user, which used for run autossh')
parser.add_argument('--user_home_dir', default='/home/autossh_py/', help='home dir of system user, which used for run autossh')
parser.add_argument('--ssh_user', default='autossh_py', help='user, which used for ssh connection to destination host')
parser.add_argument('--prefix', default='none', help='prefix as uniq name for files')
parser.add_argument('--dst_dir', default='/opt/autossh_py/', help='dir where autossh must be installed')
parser.add_argument('--src_dir', default='./', help='dir from autossm must be installed')
parser.add_argument('--noop', action='store_const', const=True, help='run without operations - only print commands')
args = parser.parse_args()

def _subprocess(cmd):
    '''Shortcut for subprocess generic code'''
    if conf.get('noop'):
        print('Command:')
        print(' '.join(cmd), end='\n\n\n')
        return
    proc = Popen(cmd, stdout=None, stderr=PIPE)
    out = proc.communicate()
    returncode = proc.wait()
    if out[1]:
        for line in out[1].decode('UTF-8', errors='replace').split('\n'):
            print('stderr of "{0}" is: {1}'.format(' '.join(cmd), line))
        print('Return code of "{0}" is: {1}'.format(' '.join(cmd), returncode))
    
def parse_args():
    '''Parse configuration from config and cmd'''
    # init config dictionary
    conf = dict()
    # add parsed args to config dictionary
    for key in vars(args):
        if vars(args)[key]:
            conf[key] = vars(args)[key]
    # set default prefix to destination hostname if none
    if conf['prefix'] == 'none':
        conf['prefix'] = conf['host']
    # add separator after pefix
    if conf['prefix'][-1] != '_':
        conf['prefix'] = conf['prefix'] + '_'
    if conf.get('noop'):
        print('Parsed args:')
        for key in conf:
            print('{0}: {1}'.format(key, conf[key]))
        print('\n')
    return conf

def copy_all():
    '''Copy source code directory to destination'''
    cmd = 'cp -r {0} {1}'.format(conf['src_dir'], conf['dst_dir'])
    if not os.path.isdir(conf['dst_dir']):
        _subprocess(cmd.split())
    else:
        print('Directory {0} already exist - will add only generated configs '.format(conf['dst_dir']))

def add_config():
    '''Generate autossh config from template'''
    src_file_name = conf['src_dir'] + '/autossh.py.conf.base'
    dst_file_name = '{0}{1}autossh.py.conf'.format(conf['dst_dir'], conf['prefix'])
    variables = ['ssh_user', 'host', 'prefix', 'user_home_dir']
    tmp_file = list()
    with open(src_file_name) as src_file:
        for line in src_file:
            for var in variables:
                tmp_var = '{{' + var + '}}'
                if line.find(tmp_var) != -1:
                    line = line.replace(tmp_var, conf[var])
            tmp_file.append(line)
    if conf.get('noop'):
        print('Generate file "{0}" from template:'.format(dst_file_name))
        for line in tmp_file:
            print(line, end="")
        print('\n')
        return dst_file_name
    else:
        print('Generating file {0}'.format(dst_file_name))
    with open(dst_file_name, 'w') as dst_file:
        for line in tmp_file:
            dst_file.write(line)
    return dst_file_name

def add_systemd_script():
    '''Generate systemd config from template'''
    src_file_name = '{0}autossh_py.service.base'.format(conf['src_dir'])
    dst_file_name = '/etc/systemd/system/{0}autossh_py.service'.format(conf['prefix'])
    tmp_file = list()
    variables = ['user', 'dst_dir', 'config_name']
    with open(src_file_name) as src_file:
        for line in src_file:
            for var in variables:
                tmp_var = '{{' + var + '}}'
                if line.find(tmp_var) != -1:
                    line = line.replace(tmp_var, conf[var])
            tmp_file.append(line)
    if conf.get('noop'):
        print('Generate file "{0}" from template:'.format(dst_file_name))
        for line in tmp_file:
            print(line, end="")
        print('\n')
        return
    else:
        print('Generating file {0}'.format(dst_file_name))
    with open(dst_file_name, 'w') as dst_file:
        for line in tmp_file:
            dst_file.write(line)

def enable_autostart():
    '''Enable autostart in systemd'''
    _subprocess('systemctl daemon-reload'.split())
    service_name = '{0}autossh_py.service'.format(conf['prefix'])
    cmd = 'systemctl enable {0}'.format(service_name)
    _subprocess(cmd.split())

def add_user():
    '''Add system user for autossh if not exist'''
    cmd = 'useradd -m -d {0} {1}'.format(conf['user_home_dir'], conf['user'])
    try:
        pwd.getpwnam(conf['user'])
    except KeyError:
        _subprocess(cmd.split())

def create_ssh_key():
    '''Add ssh key for autossh if not exist'''
    ssh_dir = conf['user_home_dir'] + '.ssh/'
    if not os.path.isdir(ssh_dir):
        cmd = 'mkdir ' + ssh_dir
        _subprocess(cmd.split())
    key_name = '{0}.ssh/autossh_py_rsa'.format(conf['user_home_dir'])
    if os.path.isfile(key_name):
        print('Ssh key: "{0}" alredy exist'.format(key_name))
    else:
        cmd = 'ssh-keygen -f {0} -t rsa -q -N'.format(key_name)
        _subprocess(cmd.split() + [''])

def fix_home_permissions():
    cmd = 'chown -R {0}:{0} {1}'.format(conf['user'], conf['user_home_dir'])
    _subprocess(cmd.split())

def print_final_instructions():
    # ssh key
    pub_key_file_name = '{0}.ssh/autossh_py_rsa.pub'.format(conf['user_home_dir'])
    if conf.get('noop'):
        pub_key = 'noop_pub_key'
        #hostname = 'noop_hostname'
        with open('/proc/sys/kernel/hostname') as hostname_file:
            hostname = hostname_file.read().rstrip()
    else:
        with open(pub_key_file_name) as pub_key_file:
            pub_key = pub_key_file.read().rstrip()
        with open('/proc/sys/kernel/hostname') as hostname_file:
            hostname = hostname_file.read().rstrip()
    print('\n\nNow login to your destination server:')
    print('ssh root@{1}'.format(conf['user'], conf['host']))
    print('\n\nRun next commands on destination server:')
    print('useradd -m -d /home/{0} {0}'.format(conf['user']))
    print('git clone https://github.com/gelo22/autossh.py.git /home/{0}/autossh.py'.format(conf['user']))
    print('mkdir /home/{0}/.ssh'.format(conf['user']))
    print('echo "command=\\"cd autossh.py && ./connection_tester.py --hostname=\'{0}\'\\" {1}" >> /home/{2}/.ssh/authorized_keys'.format(hostname, pub_key, conf['user']))
    print('chown -R {0}:{0} /home/{0}/'.format(conf['user']))
    print('chmod 700 /home/{0}/.ssh/'.format(conf['user']))
    print('chmod 600 /home/{0}/.ssh/authorized_keys'.format(conf['user']))
    print('\n\nFollow further instructions:\n')
    print('Edit port forwarding section("ssh_forwards") in config on client:\nsudo -e {0}{1}autossh.py.conf\n'.format(conf['dst_dir'], conf['prefix']))
    print('Start service on client:\nsudo systemctl restart {0}autossh_py.service\n'.format(conf['prefix']))

def uninstall():
    pass

if __name__ == '__main__':
    conf = parse_args()
    copy_all()
    conf['config_name'] = add_config()
    add_systemd_script()
    enable_autostart()
    add_user()
    create_ssh_key()
    fix_home_permissions()
    print_final_instructions()

