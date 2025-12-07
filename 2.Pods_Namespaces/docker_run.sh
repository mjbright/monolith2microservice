
if [ "$1" = "-rm" ]; then
    docker rm -f store1
    docker rm -f store2
    docker rm -f store3
    exit
fi

docker run -d --name store1 mjbright/flask-store:v1
docker run -d --name store2 mjbright/flask-store:v2
docker run -d --name store3 mjbright/flask-store:v3

#docker inspect store1 | grep -i address
IP1=$( docker inspect store1 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )
IP2=$( docker inspect store2 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )
IP3=$( docker inspect store3 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )

echo "Browse to http://$IP1:5000"
echo "Browse to http://$IP2:5000"
echo "Browse to http://$IP3:5000"



