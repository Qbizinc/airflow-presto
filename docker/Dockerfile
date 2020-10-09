FROM centos:centos7
LABEL maintainer="Presto community <https://prestosql.io/community.html>"

# yum -y -q install  && \
ENV JAVA_HOME /usr/lib/jvm/java-11
ARG PRESTO_VERSION=339
RUN \
    set -xeu && \
    yum -y -q update && \
    yum -y -q install epel-release && \
    yum -y -q install java-11-openjdk-devel less wget curl unzip python-pip && \
    yum -q clean all && \
    rm -rf /var/cache/yum && \
    rm -rf /tmp/* /var/tmp/* && \
    groupadd presto --gid 1000 && \
    useradd presto --uid 1000 --gid 1000 && \
    mkdir -p /usr/lib/presto /data/presto && \
    chown -R "presto:presto" /usr/lib/presto /data/presto


RUN wget -q -O /usr/lib/presto/presto-server-${PRESTO_VERSION}.tar.gz https://repo1.maven.org/maven2/io/prestosql/presto-server/${PRESTO_VERSION}/presto-server-${PRESTO_VERSION}.tar.gz
RUN tar -xvzf /usr/lib/presto/presto-server-${PRESTO_VERSION}.tar.gz -C /usr/lib/presto/ --strip 1
RUN wget -q -O /usr/lib/presto/presto-cli-${PRESTO_VERSION}-executable.jar https://repo1.maven.org/maven2/io/prestosql/presto-cli/${PRESTO_VERSION}/presto-cli-${PRESTO_VERSION}-executable.jar
RUN cp /usr/lib/presto/presto-cli-${PRESTO_VERSION}-executable.jar /usr/bin/presto
RUN chmod +x /usr/bin/presto
COPY bin/ /usr/lib/presto/bin/
COPY default/ /usr/lib/presto/default
RUN chown -R presto:presto /usr/lib/presto
RUN ls -la /usr/bin/presto
RUN ln -s /usr/lib/presto/default/etc/catalog /usr/lib/presto/default/etc/coordinator/catalog
RUN mkdir -p /etc/sysconfig/network-scripts/
RUN ln -s /usr/lib/presto/default/etc/catalog /usr/lib/presto/default/etc/worker/catalog
RUN echo "DHCP_HOSTNAME=presto-coordinator" >> /etc/sysconfig/network-scripts/ifcfg-eth0

RUN pip install --upgrade pip && \
    pip install awscli

EXPOSE 8080
USER presto:presto
ENV LANG en_US.UTF-8

# Test AWS
RUN aws --version

RUN chmod +x /usr/lib/presto/bin/run-presto
CMD [ "/usr/lib/presto/bin/run-ecs-presto" ]
