set -x -e
docker build -t mytst . 
docker stop test1 || true
docker rm test1 || true

docker run -u root -e FLUENTD_OPT=-vv -e with_forward=192.168.2.5 --name=test1 -ti --entrypoint=sh  mytst

