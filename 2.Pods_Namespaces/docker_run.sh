
MODE=store
MODE=quiz
MODE=survey

if [ "$1" = "-rm" ]; then
    docker rm -f ${MODE}1
    docker rm -f ${MODE}2
    docker rm -f ${MODE}3
    exit
fi

docker run -d --name ${MODE}1 mjbright/flask-${MODE}:v1
docker run -d --name ${MODE}2 mjbright/flask-${MODE}:v2
docker run -d --name ${MODE}3 mjbright/flask-${MODE}:v3

#docker inspect ${MODE}1 | grep -i address
IP1=$( docker inspect ${MODE}1 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )
IP2=$( docker inspect ${MODE}2 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )
IP3=$( docker inspect ${MODE}3 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )

echo "$MODE:"
echo "  Browse to http://$IP1:5000"
echo "  Browse to http://$IP2:5000"
echo "  Browse to http://$IP3:5000"



