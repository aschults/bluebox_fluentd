set -x -e
docker build -t mytst . 
docker stop test1 || true
docker rm test1 || true

# logger --rfc3164 -d -i xxx -n localhost -P 11514 -t url_fwd asdf444444


docker run -u root -e with_syslog=1 -p 11514:5140/udp -e FLUENTD_OPT=-vv -e with_a_duplication=1 -e with_filesystem=1 -e with_a_nagios_cmd=1 -e nagios_url=http://nagiosadmin:nagiosadmin@nagios/nagios -v $PWD/test/conf_custom.d:/fluentd/etc/conf_custom.d --name=test1 -ti --entrypoint=sh  mytst

