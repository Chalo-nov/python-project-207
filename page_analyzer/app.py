import os
import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)
import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv
from urllib.parse import urlparse
import validators
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


@app.route('/')
def index():
    return render_template('index.html')

from flask import Flask, render_template

app = Flask(__name__)


@app.post('/urls')
def add_url():
    url_input = request.form.to_dict().get('url', {}).get('name', '').strip()
    
    # Validar si es una URL válida
    if not url_input or not validators.url(url_input) or len(url_input) > 255:
        flash('Некорректный URL' if 'ru' in url_input else 'URL inválido', 'danger')
        return render_template('index.html', url_input=url_input), 422

    parsed_url = urlparse(url_input)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE name = %s;", (normalized_url,))
        existing_url = cursor.fetchone()

        if existing_url:
            flash('Страница уже существует' if 'ru' in url_input else 'La página ya existe', 'info')
            url_id = existing_url.id
        else:
            cursor.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;",
                (normalized_url,)
            )
            url_id = cursor.fetchone().id
            conn.commit()
            flash('Страница успешно добавлена' if 'ru' in url_input else 'Página agregada exitosamente', 'success')

    conn.close()
    return redirect(url_for('show_url', id=url_id))


@app.route('/urls')
def list_urls():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT urls.id, urls.name, 
                   url_checks.created_at as last_check_at, 
                   url_checks.status_code 
            FROM urls 
            LEFT JOIN url_checks ON urls.id = url_checks.url_id 
            WHERE url_checks.id = (
                SELECT MAX(id) FROM url_checks WHERE url_id = urls.id
            )
            OR url_checks.id IS NULL
            ORDER BY urls.id DESC;
        """)
        urls = cursor.fetchall()
    conn.close()
    return render_template('urls/index.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cursor.fetchone()
        if not url:
            abort(404)

        cursor.execute(
            "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;",
            (id,)
        )
        checks = cursor.fetchall()
    conn.close()
    return render_template('urls/show.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def check_url(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = cursor.fetchone()
        if not url:
            abort(404)

    try:
        response = requests.get(url.name, timeout=5)
        response.raise_for_status()
        status_code = response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else ''
        title = soup.title.string if soup.title else ''
        description = ''
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            description = desc_tag.get('content')

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW());
                """,
                (id, status_code, h1, title, description)
            )
            conn.commit()
        flash('Страница успешно проверена' if 'ru' in url_input else 'Página verificada exitosamente', 'success')
    except requests.RequestException:
        flash('Произошла ошибка при проверке' if 'ru' in url_input else 'Ocurrió un error al verificar la página', 'danger')

    conn.close()
    return redirect(url_for('show_url', id=id))