from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
  return '¡Hola Flask!'

@app.route('/urls')
def urls():
  return 'Página de URLs', 200