#!/bin/sh
npm install
pip install --upgrade pip
pip install -U -r requirements_for_test.txt
npm run frontend-build:production
git log --pretty=format:'%h' -n 1 > version_label