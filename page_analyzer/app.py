Flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '¡Hola Flask!'

@app.route('/urls')
def urls():
    # Aquí puedes devolver una página, un texto o incluso redirigir
    return "Página de URLs", 200