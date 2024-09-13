# quit if any step fail
set -e

INSTALL_DIR=/app/Colonizer

# check if root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# install via apt
apt install -y python3-pip python3-opencv
apt install -y unixodbc unixodbc-dev git
apt install -y nginx supervisor

# clone source code from git
cd /app
git clone git@github.com:elenhinan/Colonizer.git $INSTALL_DIR

# install python packages
pip install -r requirements.txt

# setup nginx and supervisor
cp -rv install/etc/* /etc/
ln -s /etc/nginx/sites-available/colonizer /etc/nginx/sites-enabled/colonizer
rm /etc/nginx/sites-enabled/default
systemctl disable nginx

# download and compile freetds (more recent version)
cd /tmp
wget -nv ftp://ftp.freetds.org/pub/freetds/stable/freetds-patched.tar.gz \
&& tar -zxvf freetds-patched.tar.gz \
&& cd freetds* \
&& ./configure --prefix=/usr --sysconfdir=/etc --with-unixodbc=/usr --with-tdsver=7.4 \
&& make \
&& sudo make install \
&& cd samples \
&& sudo odbcinst -i -d -f unixodbc.freetds.driver.template

# install bootstrap 4.6
BOOTSTRAP_DIR=$INSTALL_DIR/webdaemon/static/jquery
mkdir -p $BOOTSTRAP_DIR
wget https://github.com/twbs/bootstrap/archive/v4.6.2.zip
unzip v4.6.2.zip
cp -r bootstrap-4.6.2/dist/* $BOOTSTRAP_DIR
cp -r bootstrap-4.6.2/scss $BOOTSTRAP_DIR

# install jquery
JQUERY_DIR=$INSTALL_DIR/webdaemon/static/jquery
mkdir -p $JQUERY_DIR
wget -nv https://code.jquery.com/jquery-3.7.1.min.js -P $JQUERY_DIR -O jquery.min.js
wget -nv https://code.jquery.com/jquery-3.7.1.js -P $JQUERY_DIR -O jquery.js
wget -nv https://code.jquery.com/jquery-3.7.1.min.map -P $JQUERY_DIR -O jquery.min.map

# install fontawesome 5
wget -nv https://use.fontawesome.com/releases/v5.15.4/fontawesome-free-5.15.4-web.zip
unzip fontawesome-free-5.15.4-web.zip
mv fontawesome-free-5.15.4-web $INSTALL_DIR/webdaemon/static/fontawesome

# install tensorflow js
TF_DIR=$INSTALL_DIR/webdaemon/static/tensorflow
mkdir -p $TF_DIR
wget -nv https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@3.9/dist/tf.min.js -P $TF_DIR
wget -nv https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@3.9/dist/tf.min.js.map -P $TF_DIR

# install jsoneditor js
JE_DIR=$INSTALL_DIR/webdaemon/static/jsoneditor
mkdir -p $JE_DIR $JE_DIR/img
wget -nv https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/10.1.0/jsoneditor.js -P $JE_DIR
wget -nv https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/10.1.0/jsoneditor.map -P $JE_DIR
wget -nv https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/10.1.0/jsoneditor.css -P $JE_DIR
wget -nv https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/10.1.0/img/jsoneditor-icons.svg $JE_DIR/img

# install sass
cd /tmp
wget https://github.com/sass/dart-sass/releases/download/1.77.5/dart-sass-1.77.5-linux-arm64.tar.gz
unzip dart-sass-1.77.5-linux-arm64.tar.gz
mv dart-sass $INSTALL_DIR/sass

# compile css
cd $INSTALL_DIR/webdaemon/static
$INSTALL_DIR/sass/sass scss/bs_theme.scss css/bootstrap_themed.css

# create folder for smb share
mkdir -p /mnt/data

# setup auto-remount in crontab
sudo crontab -e
add "*/5 * * * * grep -q "/mnt/petra" /proc/mounts || sudo mount /mnt/petra"
sudo pico /etc/fstab
add "//yourfileserver/sharename  /mnt/data      cifs    noserverino,credentials=/home/pi/.smbcredentials    0    0"
add "username=<username>\npassword=<password>" to ~/.smbcredentials

# set permissions
sudo chown colonizer:www-data /mnt/data
sudo chmo 770 /mnt/data
sudo chown colonizer:www-data -R $INSTALL_DIR
sudo find $INSTALL_DIR -type f -exec chmod 640 {} \;
sudo find $INSTALL_DIR -type d -exec chmod 750 {} \;