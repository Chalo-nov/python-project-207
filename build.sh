#!/usr/bin/env bash

curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# postgres se conecta con -d y la URL se lee desde DATABASE_URL
make install && psql -a -d $DATABASE_URL -f database.sql