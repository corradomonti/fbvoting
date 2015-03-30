export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get -y upgrade
apt-get -y install python-software-properties debconf-utils apache2 curl build-essential python-dev redis-server libssl-dev ne

# add java repo and keys
add-apt-repository ppa:webupd8team/java
echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10

# add mongo repo
echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' > /etc/apt/sources.list.d/mongodb.list

### add packages 

apt-get update

apt-get -y install oracle-java7-installer
apt-get -y install mongodb-10gen
apt-get -y install mercurial

### python and venv

curl -sLo /tmp/get-pip.py https://raw.github.com/pypa/pip/master/contrib/get-pip.py
python /tmp/get-pip.py
pip install virtualenv
pip install virtualenvwrapper

### configure fbvoting home 

rm -rf /home/vagrant/fbvoting /home/vagrant/.pip /home/vagrant/.ssh/id_rsa /tmp/bootstrap.sh

cat <<EOF >/home/vagrant/.ssh/config
NoHostAuthenticationForLocalhost yes
StrictHostKeyChecking no
UserKnownHostsFile /dev/null
EOF

chown vagrant:vagrant /home/vagrant/.ssh/config

cp /vagrant/id_rsa /home/vagrant/.ssh && chown vagrant:vagrant /home/vagrant/.ssh/id_rsa
cp /vagrant/id_rsa.pub /home/vagrant/.ssh && chown vagrant:vagrant /home/vagrant/.ssh/id_rsa.pub
chmod 600 /home/vagrant/.ssh/id_rsa
chmod 600 /home/vagrant/.ssh/id_rsa.pub 

### setup cron job for ranking
cat <<EOF >/etc/cron.hourly/doranking
#!/bin/bash
{ export TZ=Europe/Rome; cd /home/vagrant/fbvoting/java && java -jar fbvoting-Main.jar && echo "Cleaning redis cache..." && redis-cli FLUSHALL && echo "Last ranking completed at $(date)"; } >/home/vagrant/fbvoting/logging/ranking.log 2>&1
EOF

chmod u+x /etc/cron.hourly/doranking

