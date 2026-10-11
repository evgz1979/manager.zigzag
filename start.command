#!/bin/zsh
cd "$(dirname "$0")"
port=$(/usr/bin/python3 -c 'import server; print(server.SERVER_PORT)')
open "http://127.0.0.1:$port"
exec /usr/bin/python3 server.py
