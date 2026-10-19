#!/bin/zsh
cd "$(dirname "$0")"
url=$(/usr/bin/python3 -c 'import configparser; c=configparser.ConfigParser(interpolation=None); c.read("deploy.ini"); print("http://" + c["m4"]["ssh"].split("@")[-1] + ":" + c["m4"]["port"])')
exec /usr/bin/open "$url"
