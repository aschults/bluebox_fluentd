FROM fluent/fluentd

RUN fluent-gem install fluent-plugin-forest fluent-plugin-rewrite-tag-filter

USER root
RUN apk update && apk add python py-pip py-dateutil
RUN pip install requests
USER fluent

EXPOSE 24224 5140
EXPOSE 5140/udp

RUN mkdir -p /fluentd/log /fluentd/log_sources /fluentd/etc/conf.d /fluentd/etc/start.d
VOLUME ["/fluentd/log","/fluentd/log_sources"]

COPY url_fwd.py nagios_cmd.txt /fluentd/etc/
COPY fluent.conf /fluentd/etc/
COPY conf /fluentd/etc/conf.d
ADD start.sh /
ADD lib.sh /

USER root

#ADD liveness_check.sh /

WORKDIR /
ENTRYPOINT sh start.sh
