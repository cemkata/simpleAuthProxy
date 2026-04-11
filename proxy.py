from flask import Flask, Response, request
from requests.auth import HTTPBasicAuth
import json
import requests
import time

app = Flask(__name__, static_url_path = '/#')

with open("proxy_config.json", "r", encoding="utf-8") as f:
    data = json.load(f)

auch_protocol = data['authentication_server']['protocol']
auch_server =   data['authentication_server']['ip']
auch_port =     data['authentication_server']['port']
auth_username = data['authentication_server']['auth_username']
auth_password = data['authentication_server']['auth_password']

dest_protocol = data['proxy_server']['destination_server']['protocol']
dest_server =   data['proxy_server']['destination_server']['ip']
dest_port =     data['proxy_server']['destination_server']['port']

# ===== Helpers =====
def cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE, PATCH, OPTIONS'
    return resp

def check_login(request):
    auth_req = requests.get(f'{auch_protocol}://{auch_server}:{auch_port}/protected', allow_redirects=False, headers=request.headers)
    authenticated = False
    if auth_req.status_code != 200:
        if request.path == "/login":
            targer_url = f'{auch_protocol}://{auch_server}:{auch_port}' + "/login"
        else:
            targer_url = f'{auch_protocol}://{auch_server}:{auch_port}'
    else:
        if request.path == "/logout" or request.path == "/logoff": 
            targer_url = f'{auch_protocol}://{auch_server}:{auch_port}' + "/logout"
        else:
            if request.path == "/login":
                targer_url = f'{dest_protocol}://{auch_server}:{dest_port}'
                #targer_url = f'{dest_protocol}://{dest_server}:{dest_port}'
            else:
                authenticated = True
                targer_url = f'{dest_protocol}://{dest_server}:{dest_port}' + request.full_path
    return (targer_url, authenticated)

def proccess_response(req, authenticated, origin_server):
    return_data = req.content
    if req.status_code != 200:
        new_headers = {}
        for key in req.headers:
            new_headers.update({
                key: req.headers[key],
            })
        try:
            if (dest_protocol == 'http' and dest_port == '80') or (dest_protocol == 'https' and dest_port == '443'):
                new_headers['Location'] = req.headers['Location'].replace(f"{dest_protocol}://{dest_server}", origin_server)
            else:
                new_headers['Location'] = req.headers['Location'].replace(f"{dest_protocol}://{dest_server}:{dest_port}", origin_server)
        except KeyError as e:
            pass
        resp = Response(req.content, status=req.status_code, content_type=req.headers['Content-Type'])
        resp.headers = new_headers
    else:
        if authenticated:
            stringToreplace = '<body'
            try:
                for ch in req.text.split(stringToreplace)[1]:
                    if ch == '>':
                        stringToreplace = stringToreplace + '>'
                        break
                    stringToreplace = stringToreplace + ch
                return_data = return_data.replace(stringToreplace.encode('utf-8'), stringToreplace.encode('utf-8')+b'<div style="background-color:LightYellow;"><a href="/logout" style="color:blue;text-align:right; float: right;" >Logoff</a><br></div>')
            except IndexError:
               request_response = req.content
        resp = Response(return_data, status=req.status_code, content_type=req.headers['Content-Type'])
    return cors(resp)

@app.route('/')
def process_index():
    return process_request('')

@app.route('/<path:url_path>', methods = ['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
def process_request(url_path):
    try:
        url, authenticated = check_login(request)
        if not authenticated:
            if url_path.startswith('static/'):
                url = f'{auch_protocol}://{auch_server}:{auch_port}/{url_path}'
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
            print(">>>Delete")
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
            req = requests.get(url,
                headers=server_request_headers,
                auth=HTTPBasicAuth(auth_username, auth_password),
                allow_redirects=False,
            )
        return proccess_response(req, authenticated, origin_server)
    except requests.exceptions.ConnectionError:
        resp = Response(json.dumps({'error': "Server not accecible"}), status=500, content_type='application/json')
        return cors(resp)
    except Exception as e:
        resp = Response(json.dumps({'error': str(e)}), status=502, content_type='application/json')
        return cors(resp)
if __name__ == '__main__':
    retries = 0
    max_retries = int(data['proxy_server']['startup_retries'])
    waitingTime = int(data['proxy_server']['waiting_time'])
    while True:
        try:
           _ = requests.get(f"{auch_protocol}://{auch_server}:{auch_port}/protected", allow_redirects=False)
           break
        except:
           if retries > max_retries:
              print("Failed to start after "+str(waitingTime * retries)+" seconds")
              print("And "+str(retries)+" retries!")
              exit(255)
           retries +=1
           time.sleep(waitingTime)
    app.run(host=data['proxy_server']['ip'], port=int(data['proxy_server']['port']), debug=True)
    # In production, run via a WSGI server (gunicorn, waitress, uWSGI)
