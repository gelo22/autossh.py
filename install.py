#!/usr/bin/env python

import shutil
import os
import sys

def run():
    src_dir = os.path.dirname(sys.argv[0])
    dst_dir = '/opt/autossh_py/'
    if not os.path.isdir(dst_dir):
        shutil.copytree(src_dir, dst_dir)
    else:
        print('Directory {0} already exist'.format(dst_dir))

    src_file = src_dir + '/autossh_py.service'
    dst_file = '/etc/systemd/system/autossh_py.service'
    if not os.path.isfile(dst_file):
        shutil.copy(src_file, dst_file)
    else:
        print('File {0} already exist'.format(dst_dir))

if __name__ == '__main__':
    run()

