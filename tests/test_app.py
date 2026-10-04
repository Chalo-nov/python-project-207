from page_analyzer.app import app

def test_index():
    client = app. test_client()
    response = client.get('/')
    assert response.status_code == 200

def test_urls_route():
    client = app.test_client()
    response = client.get('/urls')
    # Dependiendo de tu implementación inicial, puede retornar 200 o redirigir
    assert response.status_code in [200, 302]