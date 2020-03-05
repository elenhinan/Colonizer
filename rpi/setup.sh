#!/bin/bash
# setup raspi-config
# generate locale and set default
# setup wifi
# enable camera

cd /tmp

# create ssh key
mkdir ~/.ssh \
&& chmod 700 ~/.ssh \
&& cd ~/.ssh \
&& ssh-keygen -f colonizer -P "" \
&& cat colonizer.pub > authorized_keys \
&& chmod 640 authorized_keys

# setup network
cat wlan_setup >> /etc/wpa_supplicant/wpa_supplicant.conf

# update system
apt-get update && apt-get -y dist-upgrade

# install packages
apt-get -y install --no-install-recommends \
    python3 \
    python3-pip \
    python3-pyqt5 \
    python3-pyqt5.qtsql \
    qt5-default \
    libqt5sql5-odbc \
    libqt5sql5-sqlite \
    libqtgui4 \
    libgomp1 \
    libdmtx0a

# install flask
sudo python3 -m pip install flask flask-bootstrap4

# install msSQL driver (amd64)
#apt-get -y install --no-install-recommends \
#    curl \
#    apt-transport-https \
#    locales \
#    unixodbc \
#    unixodbc-bin \
#    unixodbc-dev \
#&& locale-gen en_US.UTF-8 \
#curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list
#&& apt-get update \
#&& export ACCEPT_EULA=Y \
#&& apt-get -y install --no-install-recommends \
#    msodbcsql17 \
#    mssql-tools

# download freetds (more recent version)
cd /tmp
wget ftp://ftp.freetds.org/pub/freetds/stable/freetds-patched.tar.gz \
&& tar -zxvf freetds-patched.tar.gz \
&& cd freetds* \
&& ./configure --prefix=/usr --sysconfdir=/etc --with-unixodbc=/usr --with-tdsver=7.4 \
&& make \
&& make install \
&& cd samples \
&& odbcinst -i -d -f unixodbc.freetds.driver.template

# install ids ueye driver
tar -zxvf /tmp/uEyeSDK-4.90.00-ARM_LINUX_IDS_GNUEABI_HF.tgz -C /
cp zz-ueyeusb.rules /etc/udev/rules.d/
cp /tmp/ueyeusbdrc /etc/init.d
update-rc.d ueyeusbdrc defaults

# install needed python modules
pip3 install --upgrade pip \
  && pip3 install opencv-python \
  && pip3 install pyueye \
  && pip3 install pylibdmtx \

# download needed libs
apt-get -y install --no-install-recommends \
    libatlas-base-dev \
    libjasper-dev \
    libqt4-test

# zxing barcode reader
apt-get -y install --no-install-recommends\
    maven
cd /opt
git clone https://github.com/zxing/zxing.git
cd xing
mvn install
cd javase
mvn -DskipTests package assembly:single

sudo pip3 install git+https://github.com/oostendo/python-zxing.git

# download and compile opencfu
apt-get -y install --no-install-recommends \
    build-essential \
    libopencv-dev
cd /tmp
wget -O opencfu.tgz https://downloads.sourceforge.net/project/opencfu/linux/opencfu-3.9.0.tar.gz
tar -zxvf opencfu.tgz
cd opencfu*
./configure --without-gui
make install

# install led library
cd /opt
sudo git clone https://github.com/jgarff/rpi_ws281x.git
cd rpi_ws281x
#patch main.c here
cd python
apt-get install python-dev swig
python3 ./setup.py build
python3 ./setup.py install

# give access to dma
su - pi -c 'xauth list' |\
     grep `echo $DISPLAY |\
         cut -d ':' -f 2 |\
         cut -d '.' -f 1 |\
         sed -e s/^/:/`  |\
     xargs -n 3 xauth add


# cleanup
apt-get clean \
&& rm -rf /var/lib/apt/lists/* /var/log/*