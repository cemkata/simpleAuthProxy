from flask import Flask, Response, request
import json
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__, static_url_path = '/#')

with open("proxy_config.json", "r", encoding="utf-8") as f:
    data = json.load(f)

protocol = data['destination_server']['protocol']
server = data['destination_server']['ip']
port = data['destination_server']['port']
auth_username = data['destination_server']['auth_username']
auth_password = data['destination_server']['auth_password']

# ===== Helpers =====
def cors(resp: Response) -> Response:
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE, PATCH, OPTIONS'
    return resp

@app.route('/')
def process_index():
    return process_request('')

@app.route('/<path:url_path>', methods = ['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
def process_request(url_path):
    url = f"{protocol}://{server}:{port}{request.full_path}"
    origin_server = ""
    server_request_headers = {}
    for header in request.headers:
        if header[0] == 'Host' or header[0] == 'Referer' or header[0] == 'Origin':
            if header[0] == 'Origin':
                origin_server = header[1]
            continue
        server_request_headers[header[0]] = header[1]
    if request.method == 'POST':
        req = requests.post(url,
            headers=server_request_headers,
            data = request.form,
            auth=HTTPBasicAuth(auth_username, auth_password),
            allow_redirects=False
        )
    elif request.method == 'PUT':
        req = requests.put(
            url, 
            data = request.form, 
            headers=server_request_headers,
            auth=HTTPBasicAuth(auth_username, auth_password),
            allow_redirects=False,
        )
    elif request.method == 'DELETE':
        req = requests.delete(
            url, 
            data = request.form, 
            headers=server_request_headers,
            auth=HTTPBasicAuth(auth_username, auth_password),
            allow_redirects=False,
        )
    elif request.method == 'PATCH':
        req = requests.patch(
            url, 
            data = request.form, 
            headers=server_request_headers,
            auth=HTTPBasicAuth(auth_username, auth_password),
            allow_redirects=False,
        )
    else:
        try:
            req = requests.get(url,
                headers=server_request_headers,
                auth=HTTPBasicAuth(auth_username, auth_password),
                allow_redirects=False,
            )
        except Exception as e:
            resp = Response(json.dumps({'error': str(e)}), status=502, content_type='application/json')

    if req.status_code != 200:
        new_headers = {}
        for key in req.headers:
            new_headers.update({
                key.encode("utf-8"): req.headers[key].encode("utf-8"),
            })
        try:
            if (protocol == 'http' and port == '80') or (protocol == 'https' and port == '443'):
                new_headers['Location'] = req.headers['Location'].replace(f"{protocol}://{server}", origin_server)
            else:
                new_headers['Location'] = req.headers['Location'].replace(f"{protocol}://{server}:{port}", origin_server)
        except KeyError as e:
            pass
        resp = Response(req.content, status=req.status_code, content_type=req.headers['Content-Type'])
        resp.headers = new_headers
    else:
        resp = Response(req.content, status=req.status_code, content_type=req.headers['Content-Type'])
        #resp.headers = new_headers
    return cors(resp)


if __name__ == '__main__':
    app.run(host=data['proxy_server']['ip'], port=int(data['proxy_server']['port']), debug=True)
    # In production, run via a WSGI server (gunicorn, waitress, uWSGI)
