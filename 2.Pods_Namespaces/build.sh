
cd $(dirname $0)

TMP=~/var/mono2micro.docker-builds
rm -rf   $TMP
mkdir -p $TMP

rsync -av ../1.Monoliths/* $TMP

PLAIN="--progress plain"

docker build $PLAIN -t mjbright/flask-store:v1 -f Dockerfile.1 $TMP/onlinestore
docker build $PLAIN -t mjbright/flask-store:v2 -f Dockerfile.2 $TMP/onlinestore
docker build $PLAIN -t mjbright/flask-store:v3 -f Dockerfile.3 $TMP/onlinestore


