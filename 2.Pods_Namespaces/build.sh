
cd $(dirname $0)

TMP=~/var/mono2micro.docker-builds
rm -rf   $TMP
mkdir -p $TMP

rsync -av ../1.Monoliths/* $TMP

PLAIN="--progress plain"

BUILD_MONOLITH_IMAGES_onestore() {
    ARCH=$1; shift;
    PLATFORM="--platform $ARCH"

    # Build for local architecture:
    # docker build $PLAIN -t mjbright/flask-store:v1 -f Dockerfile.1 $TMP/onlinestore
    # docker build $PLAIN -t mjbright/flask-store:v2 -f Dockerfile.2 $TMP/onlinestore
    # docker build $PLAIN -t mjbright/flask-store:v3 -f Dockerfile.3 $TMP/onlinestore

    # Build for specific architecture:
    #PLATFORM="--platform linux/amd64"
    docker build $PLAIN $PLATFORM -t mjbright/flask-store:v1 -f Dockerfile.1 $TMP/onlinestore
    docker build $PLAIN $PLATFORM -t mjbright/flask-store:v2 -f Dockerfile.2 $TMP/onlinestore
    docker build $PLAIN $PLATFORM -t mjbright/flask-store:v3 -f Dockerfile.3 $TMP/onlinestore

    case $ARCH in
        linux/amd64)
            docker login
            docker push mjbright/flask-store:v1
            docker push mjbright/flask-store:v2
            docker push mjbright/flask-store:v3
	    ;;
    esac

    # Multi-arch doesn't work with docker engine (needs containerd?):
    # - https://docs.docker.com/build/building/multi-platform/
    # docker buildx build $PLAIN --platform linux/amd64,linux/arm64 -t mjbright/flask-store:v1 -f Dockerfile.1 $TMP/onlinestore
    # docker buildx build $PLAIN --platform linux/amd64,linux/arm64 -t mjbright/flask-store:v2 -f Dockerfile.2 $TMP/onlinestore
    # docker buildx build $PLAIN --platform linux/amd64,linux/arm64 -t mjbright/flask-store:v3 -f Dockerfile.3 $TMP/onlinestore
}

# BUILD_MONOLITH_IMAGES_onestore linux/amd64
# BUILD_MONOLITH_IMAGES_onestore linux/arm64


