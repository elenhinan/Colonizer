cd
git clone git@github.com:elenhinan/Colonizer.git

sudo apt install -y python3-pip python3-opencv
sudo apt install -y unixodbc unixodbc-dev
pip install opencv-contrib-python
pip install flask
pip install bootstrap-flask
pip install fontawesome-free
pip install flask-sqlalchemy
pip install flask-fontawesome
pip install flask-session
pip install flask-wtf
pip install adafruit-circuitpython-neopixel

# download freetds (more recent version)
cd /tmp
wget ftp://ftp.freetds.org/pub/freetds/stable/freetds-patched.tar.gz \
&& tar -zxvf freetds-patched.tar.gz \
&& cd freetds* \
&& ./configure --prefix=/usr --sysconfdir=/etc --with-unixodbc=/usr --with-tdsver=7.4 \
&& make \
&& sudo make install \
&& cd samples \
&& sudo odbcinst -i -d -f unixodbc.freetds.driver.template