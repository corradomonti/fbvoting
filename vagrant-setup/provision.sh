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
apt-get -y install git

### python and venv

curl -sLo /tmp/get-pip.py https://raw.github.com/pypa/pip/master/contrib/get-pip.py
python /tmp/get-pip.py
pip install virtualenv
pip install virtualenvwrapper

### clean my home

rm -rf /home/vagrant/fbvoting /home/vagrant/.pip /tmp/bootstrap.sh

### setup cron job for ranking
cat <<EOF >/etc/cron.hourly/doranking
#!/bin/bash
{ export TZ=Europe/Rome; cd /home/vagrant/fbvoting/java && java -jar fbvoting-Main.jar && echo "Cleaning redis cache..." && redis-cli FLUSHALL && echo "Last ranking completed at $(date)"; } >/home/vagrant/fbvoting/logging/ranking.log 2>&1
EOF

chmod u+x /etc/cron.hourly/doranking

# we setup a script so that we can execute it as vagrant user (via sudo)
cat <<EOF >/tmp/bootstrap.sh
cd /home/vagrant && git clone https://github.com/corradomonti/fbvoting.git
virtualenv /home/vagrant/fbvoting/venv
cd /home/vagrant/fbvoting && chmod u+x ./deploy.sh
EOF

chmod a+rx /tmp/bootstrap.sh
sudo -u vagrant /tmp/bootstrap.sh
