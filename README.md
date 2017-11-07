### Features

Able to run ssh ports forwarding:

1. connection control for fix broken connection as soon as possible
2. daemon mode
3. systemd
4. same options in both config and command line arguments
5. client have no shell on remote host

### Ruquirements

Python 2 or Python 3

GNU/Linux

Openssh

systemd (optional, but recommended)

### Configuration

1. Clone git on client host
~~~~
git clone https://github.com/gelo22/autossh.py.git
~~~~
2. Run installer on client host
~~~~
cd autossh.py.git/
./install.py --host=router-ssh.example.com --prefix=my_prefix
~~~~
where:

--host is destination server
 
--prefix is prefix, which will be used to make uniq names across autossh clients

--user is user in client's system, which will be used for autossh client start

--ssh_user is user, which will be used for ssh connection to destination host

by default install path is /opt/autossh_py/, both users is autossh_py

3. Run automatically generated commands on server host, which you will see in ./install.py script output
~~~~
Run next commands on destination server:
...
~~~~
4. Run service
~~~~
systemctl start my_prefix_autossh_py.service
~~~~

### Run without systemd

watch all commands via --noop option and run its manually:
~~~~
./install.py --host=router-ssh.example.com --prefix=my_prefix --noop
~~~~
add job to crontab
~~~~
crontab -e
~~~~
add line
~~~~
@reboot /opt/autossh_py/autossh.py --config=/opt/autossh_py/my_prefix_autossh.py.conf
~~~~
save file and exit

### Get command line options

Config file and script have the same options, run script in help mode to get list of options:
~~~~
./autossh.py -h
~~~~

Options from command line will owerride values from config

### Remove installed files
~~~~
systemctl disable router-kiev_autossh_py.service; rm -rf /opt/autossh_py/ /etc/systemd/system/*_autossh_py.service /tmp/autossh_py/ ; userdel -r autossh_py; rm -rf /home/autossh_py/
~~~~
