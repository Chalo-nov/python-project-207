PORT ?= 8000
start:
    poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

install:
	uv sync
dev:
	uv run flask --debug --app page_analyzer:app run

install:
	poetry install

dev:
	poetry run flask --debug --app page_analyzer:app run

build:
	./build.sh

render-start:
    poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

test:
	poetry run pytest tests/


start-server:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
	