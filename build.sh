#!/usr/bin/env bash

curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

make install

# Crea la tabla en la base de datos usando Python de forma segura
python3 -c "import os, psycopg2; conn = psycopg2.connect(os.getenv('DATABASE_URL')); cur = conn.cursor(); cur.execute(open('database.sql').read()); conn.commit(); cur.close(); conn.close()"