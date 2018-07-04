# Quick Start

```
git clone https:github.com/summa-platform/summa-mt.git
cd summa-mt
make builder
make engine
make prepare
make build
```

This is a multi-stage build.

- `make builder` builds an image to compile all software
  needed for translation.
- `make engine` builds a 'blank' image that contains only
  what's needed in production, but not the models.
- `make prepare` downloads the models and sets up a docker
  build context for an image with models. I was getting
  tired of waiting for the models to download everytime I had
  to rebuild an image. You can skip this step if you want and
  go straight to
- `make build` to build image(s) including the models.

To restrict the action to a single language pair, override
LPAIRS on the command line;
```
make build LPAIRS=de-en
```

Currently only de-en is available.

