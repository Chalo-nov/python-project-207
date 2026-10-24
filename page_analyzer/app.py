import os
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)
from validators import url as validate_url

load_dotenv()

# Inicialización de la aplicación Flask (DEBE ir antes de cualquier @app.route)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret_key')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db():
    return psycopg2.connect(DATABASE_URL)


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)


@app.route('/urls', methods=['POST'])
def add_url():
    url_input = request.form.get('url')

    if not validate_url(url_input) or len(url_input) > 255:
        flash('URL no válida', 'danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template('index.html', messages=messages, url=url_input), 422

    conn = get_db()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT id FROM urls WHERE name = %s;", (url_input,))
        existing_url = cur.fetchone()

        if existing_url:
            flash('Página ya existe', 'info')
            conn.close()
            return redirect(url_for('show_url', id=existing_url['id']))

        cur.execute(
            "INSERT INTO urls (name) VALUES (%s) RETURNING id;",
            (url_input,)
        )
        new_id = cur.fetchone()['id']
        conn.commit()

    conn.close()
    flash('Página añadida con éxito', 'success')
    return redirect(url_for('show_url', id=new_id))


@app.route('/urls')
def list_urls():
    conn = get_db()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            SELECT DISTINCT ON (urls.id) 
                urls.id, 
                urls.name, 
                url_checks.created_at 
            FROM urls 
            LEFT JOIN url_checks ON urls.id = url_checks.url_id 
            ORDER BY urls.id DESC, url_checks.created_at DESC;
        """)
        urls = cur.fetchall()
    conn.close()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url_data = cur.fetchone()

        cur.execute(
            "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;",
            (id,)
        )
        checks = cur.fetchall()
    conn.close()

    if not url_data:
        return "URL no encontrada", 404

    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html', url=url_data, checks=checks, messages=messages)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    conn = get_db()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT name FROM urls WHERE id = %s;", (id,))
        url_row = cur.fetchone()

    if not url_row:
        conn.close()
        return "URL no encontrada", 404

    target_url = url_row['name']

    # Cabeceras para simular un navegador real y evitar bloqueos (como en Google)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(target_url, headers=headers, timeout=5)
        status_code = response.status_code
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('title')
        title = title_tag.string if title_tag else ''

        h1_tag = soup.find('h1')
        h1 = h1_tag.get_text() if h1_tag else ''

        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag['content'] if desc_tag and 'content' in desc_tag.attrs else ''

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO url_checks (url_id, status_code, h1, title, description)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (id, status_code, h1, title, description)
            )
            conn.commit()

        flash('Página revisada con éxito', 'success')
    except requests.exceptions.RequestException:
        flash('Falla en la comunicación o sitio no disponible', 'danger')

    conn.close()
    return redirect(url_for('show_url', id=id))