FROM fluent/fluentd

RUN fluent-gem install fluent-plugin-forest fluent-plugin-rewrite-tag-filter


EXPOSE 24224 5140
EXPOSE 5140/udp

RUN mkdir -p /fluentd/log /fluentd/log_sources /fluentd/etc/conf.d /fluentd/etc/start.d
VOLUME ["/fluentd/log","/fluentd/log_sources"]

COPY fluent.conf /fluentd/etc/
COPY conf /fluentd/etc/conf.d
ADD start.sh /
ADD lib.sh /

#ADD liveness_check.sh /

USER root
WORKDIR /
ENTRYPOINT sh start.sh
