#!/bin/sh
set -xe
npm install
./node_modules/.bin/pancake
pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install -r requirements_for_test.txt
npm run frontend-build:production
git log --pretty=format:'%h' -n 1 > version_label
