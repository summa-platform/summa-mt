#!/bin/bash

root=$(dirname $(cd $(dirname $0) && pwd))
pyscripts=$(cd $root/engine && find -name '*.py')
for f in $pyscripts; do
  cmp -s $root/engine/$f $root/docker/mt-engine/$f || echo $f
done

