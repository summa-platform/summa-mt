# Quick Start

If you are content using one of the SUMMA MT models,
the easiest way is to just pull the docker image, e.g.

```
docker pull summaplatform/mt-engine-de-en:latest
```

The following engines are available:
- summaplatform/mt-engine-de-en:latest
- summaplatform/mt-engine-es-en:latest
- summaplatform/mt-engine-fa-en:latest
- summaplatform/mt-engine-lv-en:latest
- summaplatform/mt-engine-pt-en:latest
- summaplatform/mt-engine-ru-en:latest
- summaplatform/mt-engine-uk-en:latest

The image currently provides a RabbitMQ worker
for use within the SUMMA platform and a batch translation
script for testing. For the latter, use, e.g.

```
cat source.txt | docker run --rm -i summaplatform/mt-engine-de-en ./translate.py --cpu-threads=2 [-v]
```

By default, the image uses as many threads as the host has cpus, but
models are loaded sequentially, so using more threads increases the
startup time. 

To use your own model, you can map it into the container running the
MT engine:

```
cat source.txt \
| docker run --rm -i -v /path/to/my/model:/model:ro summa-platform/mt-engine \
./translate.py --cpu-threads=2 [-v]
```



# Quick Start

The Docker image build is staged

For the MT engine image

```
git clone https:github.com/summa-platform/summa-mt.git
cd summa-mt
make image/mt-build-environment
make image/mt-marian-compiled
make image/mt-basic-engine
make image/mt-engine
```

To download all SUMMA models:

```
make models
```

To build all model images

```
make model-images
```

To build a single model image

```
make image/mt-model-${L}-en
```

Where `${L}` is one of de, es, fa, lv, pt, ru, uk.

To build all engine images

```
make engine-images
```

To build a single engine image:

```
make image/mt-engine-${L}-en
```

