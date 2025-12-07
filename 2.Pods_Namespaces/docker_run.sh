
DOCKER_RM_F() {
    MODE=$1; shift
    docker rm -f ${MODE}1
    docker rm -f ${MODE}2
    docker rm -f ${MODE}3
}

DOCKER_RUN() {
    MODE=$1; shift

    PORT1=$1
    docker run -p $1:5000 -d --name ${MODE}1 mjbright/flask-${MODE}:v1
    shift
    PORT2=$1
    docker run -p $1:5000 -d --name ${MODE}2 mjbright/flask-${MODE}:v2
    shift
    PORT3=$1
    docker run -p $1:5000 -d --name ${MODE}3 mjbright/flask-${MODE}:v3
    shift

    #docker inspect ${MODE}1 | grep -i address
    IP1=$( docker inspect ${MODE}1 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )
    IP2=$( docker inspect ${MODE}2 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )
    IP3=$( docker inspect ${MODE}3 | grep IPAddress | tail -1 | sed -e 's/.*: "//' -e 's/",//' )

    echo "$MODE:"
    echo "  Browse to http://$IP1:5000 or http://127.0.0.1:$PORT1"
    echo "  Browse to http://$IP2:5000 or http://127.0.0.1:$PORT2"
    echo "  Browse to http://$IP3:5000 or http://127.0.0.1:$PORT3"
}

#MODE=store
#MODE=quiz
#MODE=survey

if [ "$1" = "-rm" ]; then
    DOCKER_RM_F store
    DOCKER_RM_F quiz
    DOCKER_RM_F survey
    exit
fi

DOCKER_RUN store   5001 5002 5003
DOCKER_RUN quiz    6001 6002 6003
DOCKER_RUN survey  7001 7002 7003


