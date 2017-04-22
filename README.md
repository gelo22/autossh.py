### Features

Able to run ssh ports forwarding:

1. connection control for asap broken connection detection and restart
2. daemon mode
3. write logs
4. same options in both config and command line arguments
5. have no shell on remote host

### Simple run

1. Clone git
2. Create new ssh key for this script, authorize this ssh key on the destination host
3. Make your own config from example "autossh.py.conf"
4. Run script


my_server_host - client(s) will connect to this host
my_client_host - client host, which will connect to my_server_host
my_ssh_key - public ssh key which my_client_host will use for connection to my_server_host
my_user - user, which my_client_host will use for connection to my_server_host

# on the my_client_host todo:
# login as desired user, generate ssh_keys (by default id_rsa and id_rsa.pub)
ssh-keygen
# set variables
cat > my_variables <<EOF
my_server_host=server.example.com
my_client_host=client.example.com
my_user=user
my_ssh_key="./ssh/id_rsa.pub"
my_ssh_privat_key="./ssh/id_rsa"
EOF
source my_variables
scp my_variables ${my_user}@${my_server_host}:./

git clone https://github.com/gelo22/autossh.py.git
sed -i s/my_user/${my_user}/g autossh.py/autossh.py.conf
sed -i s/my_destination_host/${my_server_host}/g autossh.py/autossh.py.conf
sed -i s/my_ssh_private_key/${my_ssh_privat_key}/g autossh.py/autossh.py.conf
scp .ssh/id_rsa.pub ${my_server_host}:./

# add job to crontab
crontab -e
# add line
@reboot cd ./autossh.py/ && ./autossh.py
# save file and exit

# on the my_server_host todo:
git clone https://github.com/gelo22/autossh.py.git
old_umask=$(umask)
umask 0077
mkdir -p ./ssh
my_ssh_key_value=$(cat ./id_rsa.pub)
echo "command=\"cd autossh.py && ./connection_tester.py --hostname='${my_client_host}'\" ${my_ssh_key_value}" >> .ssh/authorized_keys 
umask $old_umask

#reboot my_client_host to check if cron started
ps aux | grep autossh

### Ruquirements

Python2 or Python3

GNU/Linux

Openssh

Config file and script have the same options:
<pre>
usage: autossh.py [-h] [--config CONFIG] [--ssh-user SSH_USER]
                  [--ssh-host SSH_HOST] [--ssh-options SSH_OPTIONS]
                  [--ssh-forwards SSH_FORWARDS] [--ssh-key SSH_KEY]
                  [--pid-file PID_FILE] [--log-file LOG_FILE]
                  [--log-level LOG_LEVEL]
                  [--connection-tester-interval CONNECTION_TESTER_INTERVAL]
                  [--disable-connection-tester DISABLE_CONNECTION_TESTER]
                  [--daemon DAEMON]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       config file location
  --ssh-user SSH_USER   ssh user for ssh connection
  --ssh-host SSH_HOST   remote host for ssh connection
  --ssh-options SSH_OPTIONS
                        additional options for ssh, for example "-tt -o
                        AddressFamily=inet -o ExitOnForwardFailure=yes"
  --ssh-forwards SSH_FORWARDS
                        forward options for ssh, for example "-R
                        2001:127.0.0.1:22"
  --ssh-key SSH_KEY     private key for ssh connection, for example
                        "/home/mu_user/.ssh/id_rsa_pf"
  --pid-file PID_FILE   pid file location
  --log-file LOG_FILE   log file location
  --log-level LOG_LEVEL
                        set output level for log messages
  --connection-tester-interval CONNECTION_TESTER_INTERVAL
                        interval for watchdog message check, will break
                        connection if control message not received
  --disable-connection-tester DISABLE_CONNECTION_TESTER
                        disable connection testing via remote script if
                        --disable-connection-tester="if_not_empty_string"
  --daemon DAEMON       enable daemon mode if --daemon="if_not_empty_string"
</pre>

Options from command line will owerride values from config

### Run with connection testing

Main adwantage - usege with connection controll, in daemon mode and without shell access on remote host

For this mode - set option disable-connection-tester="" and daemon="yes" in config

On remote server must do preparations:

copy "connection_tester.py" script to destination host
<pre>scp ./connection_tester.py root@$my_ssh_host:./</pre>
ssh to destination host and add your ssh public key
<pre>vim .ssh/authorized_keys</pre>
add your key like this example:
<pre>
command="cd autossh && ./connection_tester.py --hostname my_client_name" ssh-rsa $my_ssh_key # user
</pre>

Run script, enjoy

### Example usage

Config now in Json format:
<pre>
{
Example config and run
"ssh-user": "my_user",
"ssh-host": "my_destination_host",
"ssh-options": "-tt -o AddressFamily=inet -o ExitOnForwardFailure=yes -o ConnectTimeout=10 -o PasswordAuthentication=no",
"ssh-forwards": "-R 2001:127.0.0.1:22",
"ssh-key": "/home/my_user/.ssh/my_ssh_private_key",
"pid-file": "./autossh.py.pid",
"log-file": "./autossh.py.log",
"log-level": "info",
"connection-tester-interval": 10,
"disable-connection-tester": "",
"daemon": "yes"
}
</pre>
With this config will run as daemon with connection testing and will forward port 22 from current host to port 2001 on remote host

You can add this script to user's crontab via
<pre>crontab -e</pre>
This entry will run script every reboot
<pre>
@reboot /home/user/.scripts/autossh.py
</pre>
