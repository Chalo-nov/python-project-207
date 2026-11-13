install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run

PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
build:
	uv sync
	uv run python -c "import os, psycopg2; conn = psycopg2.connect(os.getenv('DATABASE_URL')); cur = conn.cursor(); cur.execute(open('database.sql').read()); conn.commit(); cur.close(); conn.close()"
render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app