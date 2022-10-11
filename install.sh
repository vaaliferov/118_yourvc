#!/usr/bin/env bash

source config.sh

rm -rf $DIR $SERVICE_FILE_PATH
systemctl disable --now $SERVICE_NAME

cat bot.service > $SERVICE_FILE_PATH
sed -i "s/<name>/$NAME/g" $SERVICE_FILE_PATH
sed -i "s/<user>/$USER/g" $SERVICE_FILE_PATH

mkdir $DIR $ENV_PATH $DATA_PATH
apt install -y python3-pip python3-venv
apt install -y git opus-tools
pip3 install virtualenv gdown
pip3 install ffmpeg-normalize
python3 -m venv $ENV_PATH

cp -r . $DIR

gdown --id $MODEL_FILE_ID -O $MODEL_PATH
gdown --id $CONFIG_FILE_ID -O $CONFIG_PATH
gdown --id $CONFIG_SE_FILE_ID -O $CONFIG_SE_PATH
gdown --id $TTS_SPEAKERS_FILE_ID -O $TTS_SPEAKERS_PATH
gdown --id $TTS_LANGUAGES_FILE_ID -O $TTS_LANGUAGES_PATH
gdown --id $CHECKPOINT_SE_FILE_ID -O $CHECKPOINT_SE_PATH

git clone $REPO_URL -b $REPO_BRANCH $TTS_PATH
rm -rf $TTS_PATH/.git

source $ENV_PATH/bin/activate
pip3 install --no-cache-dir cython wheel
pip3 install --no-cache-dir testresources setuptools
pip3 install --no-cache-dir -r requirements.txt
pip3 install -e $TTS_PATH
pip3 install -U numpy numba
deactivate

chmod 755 $DIR
chown -R $USER:$USER $DIR

systemctl daemon-reload
systemctl enable --now $SERVICE_NAME
