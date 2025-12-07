
cd $(dirname $0)

TMP=~/var/mono2micro.docker-builds
rm -rf   $TMP
mkdir -p $TMP

rsync -av ../../1.Monoliths/* $TMP

PLAIN="--progress plain"

die() {
    echo "$0: die - Build failed $*"
    exit 1
}

BUILD_MONOLITH_IMAGES_quiz() {
    ARCH=$1; shift;
    PLATFORM="--platform $ARCH"

    IMAGE_NAME=mjbright/flask-quiz
    APP=quiz
    DIR=$TMP/$APP

    # Build for local architecture:
    # docker build $PLAIN -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR
    # docker build $PLAIN -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR
    # docker build $PLAIN -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR

    # Build for specific architecture:
    #PLATFORM="--platform linux/amd64"
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR || die "[$ARCH] ${IMAGE_NAME}:v1"
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR || die "[$ARCH] ${IMAGE_NAME}:v2"
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR || die "[$ARCH] ${IMAGE_NAME}:v3"

    case $ARCH in
        linux/amd64)
            docker login
            docker push ${IMAGE_NAME}:v1
            docker push ${IMAGE_NAME}:v2
            docker push ${IMAGE_NAME}:v3
	    ;;
    esac

    # Multi-arch doesn't work with docker engine (needs containerd?):
    # - https://docs.docker.com/build/building/multi-platform/
    PLATFORM="--platform linux/amd64,linux/arm64"
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR
}

BUILD_MONOLITH_IMAGES_survey() {
    ARCH=$1; shift;
    PLATFORM="--platform $ARCH"

    IMAGE_NAME=mjbright/flask-survey
    APP=survey
    DIR=$TMP/$APP

    # Build for local architecture:
    # docker build $PLAIN -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR
    # docker build $PLAIN -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR
    # docker build $PLAIN -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR

    # Build for specific architecture:
    #PLATFORM="--platform linux/amd64"
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR || die "[$ARCH] ${IMAGE_NAME}:v1"
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR || die "[$ARCH] ${IMAGE_NAME}:v2"
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR || die "[$ARCH] ${IMAGE_NAME}:v3"

    case $ARCH in
        linux/amd64)
            docker login
            docker push ${IMAGE_NAME}:v1
            docker push ${IMAGE_NAME}:v2
            docker push ${IMAGE_NAME}:v3
	    ;;
    esac

    # Multi-arch doesn't work with docker engine (needs containerd?):
    # - https://docs.docker.com/build/building/multi-platform/
    PLATFORM="--platform linux/amd64,linux/arm64"
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR
}

BUILD_MONOLITH_IMAGES_onestore() {
    ARCH=$1; shift;

    PLATFORM="--platform $ARCH"
    IMAGE_NAME=mjbright/flask-store
    APP=onlinestore
    DIR=$TMP/$APP
    START_S=$SECONDS

    # Build for local architecture:
    # docker build $PLAIN -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR
    # docker build $PLAIN -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR
    # docker build $PLAIN -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR

    # Build for specific architecture:
    #PLATFORM="--platform linux/amd64"
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR
    docker build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR

    case $ARCH in
        linux/amd64)
            docker login
            docker push ${IMAGE_NAME}:v1
            docker push ${IMAGE_NAME}:v2
            docker push ${IMAGE_NAME}:v3
	    ;;
    esac

    # Multi-arch doesn't work with docker engine (needs containerd?):
    # - https://docs.docker.com/build/building/multi-platform/
    PLATFORM="--platform linux/amd64,linux/arm64"
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v1 -f Dockerfile.$APP.1 $DIR
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v2 -f Dockerfile.$APP.2 $DIR
    # docker buildx build $PLAIN $PLATFORM -t ${IMAGE_NAME}:v3 -f Dockerfile.$APP.3 $DIR

    TOOK $START_S "$IMAGE $ARCH"
}

TOOK() {
    START_S=$1; shift
    LABEL=$*

    let TOOK_S=SECONDS-START_S

    echo "Took $TOOK_S secs [$LABEL]"
}

START_S_0=$SECONDS

# Arm64:
if [ "$1" = "-local" ]; then
    BUILD_MONOLITH_IMAGES_quiz linux/arm64
    TOOK $START_S "flask-quiz linux/arm64"
    #START_S=$SECONDS
    exit
fi

BUILD_MONOLITH_IMAGES_onestore linux/amd64
BUILD_MONOLITH_IMAGES_onestore linux/arm64

BUILD_MONOLITH_IMAGES_survey linux/amd64
BUILD_MONOLITH_IMAGES_survey linux/arm64

BUILD_MONOLITH_IMAGES_quiz linux/amd64
BUILD_MONOLITH_IMAGES_quiz linux/arm64

TOOK $START_S_0 "All images"

docker image ls | grep flask- | grep -v '<none>'


