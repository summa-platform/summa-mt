# ARG MODEL_IMAGE=summaplatform/mt-model-fa-en:20180712
# FROM ${MODEL_IMAGE} as model

FROM summaplatform/mt-model-fa-en:20180712 as model
FROM summaplatform/mt-engine
ARG MT_MODEL_PATH=/model
COPY --from=model /model ${MT_MODEL_PATH}

ARG MAINTAINER
ARG GITHASH
ARG SRCLANG
ARG TRGLANG=en

LABEL MAINTAINER=${MAINTAINER}
LABEL GITHASH=${GITHASH}

ENV LANG C.UTF-8
ENV PYTHONUNBUFFERED y
ENV SRCLANG=${SRCLANG}
ENV TRGLANG=${TRGLANG}
ENV MT_MODEL_PATH=${MT_MODEL_PATH}
ENV PATH=/opt/app/engine:${PATH}
WORKDIR /opt/app/engine

# we deliberately use CMD, not ENTRYPOINT, because it's easer
# to override from the command line
# CMD ["./translate.py"]

