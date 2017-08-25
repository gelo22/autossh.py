### Features

Able to run ssh ports forwarding:

1. connection control for asap broken connection detection and restart
2. daemon mode
3. write logs
4. same options in both config and command line arguments
5. have no shell on remote host

### Example usage

1. Clone git
2. Create new ssh key for this script, authorize this ssh key on the destination host
3. Make your own config from example "autossh.py.conf"
4. Run script

my_server_host - client(s) will connect to this host
my_client_host - client host, which will connect to my_server_host
my_ssh_key - public ssh key which my_client_host will use for connection to my_server_host
my_user - user, which my_client_host will use for connection to my_server_host

#### on the my_client_host todo:

login as desired user

set variables in file "my_variables"
~~~~
editor my_variables
~~~~
~~~~
my_server_host=server.example.com
my_client_host=client.example.com
my_user=user
my_ssh_key=".ssh/id_rsa.pub"
my_ssh_privat_key=".ssh/id_rsa"
~~~~
generate ssh_keys (by default id_rsa and id_rsa.pub)
~~~~
ssh-keygen -f ${my_ssh_privat_key}
~~~~
get code and replace default values in config by values from my_variables
~~~~
source my_variables
scp my_variables ${my_user}@${my_server_host}:./

git clone https://github.com/gelo22/autossh.py.git
sed -i s#my_user#${my_user}#g autossh.py/autossh.py.conf
sed -i s#my_destination_host#${my_server_host}#g autossh.py/autossh.py.conf
sed -i s#my_ssh_private_key#${my_ssh_privat_key}#g autossh.py/autossh.py.conf
scp ${my_ssh_key} ${my_server_host}:./autossh_client_key
~~~~
add job to crontab
~~~~
crontab -e
~~~~
add line
~~~~
@reboot cd ./autossh.py/ && ./autossh.py
~~~~
save file and exit

#### on the my_server_host todo:

~~~~
source my_variables
git clone https://github.com/gelo22/autossh.py.git
old_umask=$(umask)
umask 0077
mkdir -p ./ssh
my_ssh_key_value=$(cat autossh_client_key)
echo "command=\"cd autossh.py && ./connection_tester.py --hostname='${my_client_host}'\" ${my_ssh_key_value}" >> .ssh/authorized_keys 
umask $old_umask
~~~~
reboot my_client_host to check if cron started
~~~~
ps aux | grep autossh
~~~~
by default - port 22 to 2001 will be forwarded

### Ruquirements

Python2 or Python3

GNU/Linux

Openssh

### Options

Config file and script have the same options, run script in help mode to get list of options:
~~~~
./autossh.py -h
~~~~

Options from command line will owerride values from config

