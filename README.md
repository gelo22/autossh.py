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

login as desired user, generate ssh_keys (by default id_rsa and id_rsa.pub)
<pre>
ssh-keygen
</pre>
set variables in file "my_variables"
<pre>
editor my_variables

my_server_host=server.example.com
my_client_host=client.example.com
my_user=user
my_ssh_key="./ssh/id_rsa.pub"
my_ssh_privat_key="./ssh/id_rsa"

source my_variables
scp my_variables ${my_user}@${my_server_host}:./

git clone https://github.com/gelo22/autossh.py.git
sed -i s/my_user/${my_user}/g autossh.py/autossh.py.conf
sed -i s/my_destination_host/${my_server_host}/g autossh.py/autossh.py.conf
sed -i s/my_ssh_private_key/${my_ssh_privat_key}/g autossh.py/autossh.py.conf
scp .ssh/id_rsa.pub ${my_server_host}:./
</pre>
add job to crontab
<pre>
crontab -e
</pre>
add line
<pre>
@reboot cd ./autossh.py/ && ./autossh.py
</pre>
save file and exit

#### on the my_server_host todo:

<pre>
git clone https://github.com/gelo22/autossh.py.git
old_umask=$(umask)
umask 0077
mkdir -p ./ssh
my_ssh_key_value=$(cat ./id_rsa.pub)
echo "command=\"cd autossh.py && ./connection_tester.py --hostname='${my_client_host}'\" ${my_ssh_key_value}" >> .ssh/authorized_keys 
umask $old_umask
</pre>
reboot my_client_host to check if cron started
<pre>
ps aux | grep autossh
</pre>
by default - port 22 to 2001 will be forwarded

### Ruquirements

Python2 or Python3

GNU/Linux

Openssh

### Options

Config file and script have the same options, run script in help mode to get list of options:
<pre>
./autossh.py -h
</pre>

Options from command line will owerride values from config

