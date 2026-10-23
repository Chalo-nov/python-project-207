import os
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


@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db()
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
        url_data = cur.fetchone()
    conn.close()

    if not url_data:
        return "URL no encontrada", 404

    messages = get_flashed_messages(with_categories=True)
    return render_template('url.html', url=url_data, messages=messages)