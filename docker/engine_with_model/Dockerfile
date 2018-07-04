FROM summaplatform/mt-engine
MAINTAINER Ulrich Germann <ugermann@inf.ed.ac.uk>

ARG LANG_PAIR
ENV MODEL ${LANG_PAIR}
ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED y

WORKDIR /opt/app
ADD . .
# ENTRYPOINT ["/opt/app/rabbitmq.py"]
CMD ["/opt/app/rabbitmq.py"]
