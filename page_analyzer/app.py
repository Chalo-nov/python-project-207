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

    # Simulamos un navegador real mediante los headers (User-Agent)
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