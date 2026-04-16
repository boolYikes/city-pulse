#!/bin/bash
set -e

rm -rf build
mkdir -p build/extract build/transform

# Install deps + package in Lambda-compatible env
docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.12 \
    /bin/sh -c "
    pip install . -t build/extract/ &&
    pip install . -t build/transform/
    "

# Add handlers
cp lambda/extract/handler.py build/extract/
cp lambda/transform/handler.py build/transform/

# Zip
cd build/extract && zip -r ../../lambda/extract.zip .
cd ../transform && zip -r ../../lambda/transform.zip .
