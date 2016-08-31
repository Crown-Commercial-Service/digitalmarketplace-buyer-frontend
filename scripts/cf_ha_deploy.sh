#!/bin/sh

set -ex

cf unmap-route "$APP" service.gov.au --hostname marketplace
cf push "$APP" -f service.gov.au-manifest.production.yml
cf map-route "$APP" service.gov.au --hostname marketplace
