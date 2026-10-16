import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret_key_default')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['GET'])
def urls_index():
    conn = get_db_connection()
    with conn.cursor() as curs:
        curs.execute(
            """
            SELECT urls.id, urls.name, 
                   url_checks.created_at, url_checks.status_code 
            FROM urls 
            LEFT JOIN (
                SELECT DISTINCT ON (url_id) * 
                FROM url_checks 
                ORDER BY url_id, created_at DESC
            ) AS url_checks ON urls.id = url_checks.url_id 
            ORDER BY urls.id DESC;
            """
        )
        urls = curs.fetchall()
    conn.close()
    return render_template('urls/index.html', urls=urls)


@app.route('/urls', methods=['POST'])
def urls_post():
    url_data = request.form.get('url', {})
    name = url_data.get('name', '').strip()

    # Validación básica de URL
    if not name or len(name) > 255:
        flash('URL inválida', 'danger')
        return render_template('index.html', url={'name': name}), 422

    conn = get_db_connection()
    with conn.cursor() as curs:
        curs.execute("SELECT id FROM urls WHERE name = %s;", (name,))
        existing_url = curs.fetchone()

        if existing_url:
            flash('La URL ya existe', 'info')
            url_id = existing_url['id']
        else:
            curs.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;",
                (name,)
            )
            url_id = curs.fetchone()['id']
            conn.commit()
            flash('URL agregada con éxito', 'success')

    conn.close()
    return redirect(url_for('urls_show', id=url_id))


@app.route('/urls/<int:id>', methods=['GET'])
def urls_show(id):
    conn = get_db_connection()
    with conn.cursor() as curs:
        curs.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url = curs.fetchone()

        if not url:
            conn.close()
            return "URL no encontrada", 404

        curs.execute(
            "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;",
            (id,)
        )
        checks = curs.fetchall()

    conn.close()
    return render_template('urls/show.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def urls_check(id):
    conn = get_db_connection()
    with conn.cursor() as curs:
        curs.execute("SELECT name FROM urls WHERE id = %s;", (id,))
        url_row = curs.fetchone()

        if not url_row:
            conn.close()
            return "URL no encontrada", 404

        url_name = url_row['name']

    try:
        response = requests.get(url_name, timeout=5)
        status_code = response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('title')
        title = title_tag.string if title_tag else ''

        h1_tag = soup.find('h1')
        h1 = h1_tag.string if h1_tag else ''

        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag.get('content', '') if desc_tag else ''

        with conn.cursor() as curs:
            curs.execute(
                """
                INSERT INTO url_checks 
                (url_id, status_code, h1, title, description, created_at) 
                VALUES (%s, %s, %s, %s, %s, NOW());
                """,
                (id, status_code, h1, title, description)
            )
            conn.commit()
        flash('Página verificada con éxito', 'success')
    except requests.RequestException:
        flash('Fallo al conectar con la página', 'danger')

    conn.close()
    return redirect(url_for('urls_show', id=id))


if __name__ == '__main__':
    app.run(debug=True)