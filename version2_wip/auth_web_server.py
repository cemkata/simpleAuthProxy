from flask import Flask, render_template
from flask_basicauth import BasicAuth

import json
with open("proxy_config.json", "r", encoding="utf-8") as f:
    data = json.load(f)

app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = data['destination_server']['auth_username']
app.config['BASIC_AUTH_PASSWORD'] = data['destination_server']['auth_password']

basic_auth = BasicAuth(app)

@app.route('/secret')
@basic_auth.required
def secret_view():
    return "Working"


if __name__ == '__main__':
    app.run(host=data['destination_server']['ip'], port=int(data['destination_server']['port']), debug=True)
    # In production, run via a WSGI server (gunicorn, waitress, uWSGI)
