#!/usr/bin/env bash

# Instala las dependencias usando Poetry y el poetry.lock existente
poetry install

# Crea la tabla en la base de datos usando el entorno virtual de Poetry
poetry run python -c "import os, psycopg2; conn = psycopg2.connect(os.getenv('DATABASE_URL')); cur = conn.cursor(); cur.execute(open('database.sql').read()); conn.commit(); cur.close(); conn.close()"