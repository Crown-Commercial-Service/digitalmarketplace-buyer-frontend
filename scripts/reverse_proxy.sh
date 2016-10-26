#!/bin/sh

LIGHTTPD=`which lighttpd`

CONF=lighttpd.conf

echo "Serving on"
fgrep server.bind "$CONF"
fgrep server.port "$CONF"
echo

"$LIGHTTPD" -D -f "$CONF"
