
using mbedtls

# install

## ubuntu 
sudo apt update
sudo apt-get install libmbedtls-dev

## OL8 
 
 sudo dnf install mbedtls-devel -y

# compile
gcc mbb.c   -o upload_to_bucket -lmbedtls -lmbedx509 -lmbedcrypto         

# usage

./upload_to_bucket yewen.mp4

you will find your files in your bucket

