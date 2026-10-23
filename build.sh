#!/usr/bin/env bash

# Instala uv y dependencias
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

uv sync

# Ejecuta la creación de tablas automáticamente en la base de datos de Render
python3 -c "import os, psycopg2; conn = psycopg2.connect(os.getenv('DATABASE_URL')); cur = conn.cursor(); cur.execute(open('database.sql').read()); conn.commit(); cur.close(); conn.close()"