import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
    return '''\
<!doctype html>
<title>hello, flask</title>
<h1>hello, flask</h1>
'''
