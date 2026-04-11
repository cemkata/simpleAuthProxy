# -*- coding: utf-8 -*-
import logging
import requests
from http.client import responses as http_responses
from typing import List, Tuple, Dict, Optional, Any

from proxy.http.parser import HttpParser
from proxy.http.server import HttpWebServerBasePlugin, httpProtocolTypes
from proxy.http.responses import okResponse
from proxy.http.websocket.frame import WebsocketFrame
from proxy.common.utils import build_http_response

logger = logging.getLogger(__name__)

def tupelToDicts(inDic):
    retrunDict={}
    for key in list(inDic.keys()):
        if type(inDic[key]) == tuple:
           retrunDict[inDic[key][0].decode("utf-8")] = inDic[key][1].decode("utf-8")
        else:
            retrunDict[key.decode("utf-8")] = inDic[key].decode("utf-8")
    return retrunDict

class WebServerPlugin(HttpWebServerBasePlugin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.destinationIP = "$destinationIP"
        self.destinationPort = "$destinationPort"
        self.destinationProtocol = "$destinationProtocol"
        self.destinationIPAuth = "$destinationIPAuth"
        self.destinationPortAuth = "$destinationPortAuth"
        self.destinationProtocolAuth = "$destinationProtocolAuth"

    def routes(self) -> List[Tuple[int, str]]:
        return [
            (httpProtocolTypes.HTTP, r'^/'),
            (httpProtocolTypes.HTTPS, r'^/'),
            (httpProtocolTypes.WEBSOCKET, r'^/'),
        ]

    def handle_request(self, request: HttpParser) -> None:
        auth_req = requests.get(f'{self.destinationProtocolAuth}://{self.destinationIPAuth}:{self.destinationPortAuth}/protected', allow_redirects=False, headers=tupelToDicts(request.headers))
        authenticated = False
        if auth_req.status_code != 200:
            if request.path.decode("utf-8") == "/login":
                targer_url = f'{self.destinationProtocolAuth}://{self.destinationIPAuth}:{self.destinationPortAuth}' + "/login"
            else:
                targer_url = f'{self.destinationProtocolAuth}://{self.destinationIPAuth}:{self.destinationPortAuth}'
        else:
            if request.path.decode("utf-8") == "/logout" or request.path.decode("utf-8") == "/logoff": 
                targer_url = f'{self.destinationProtocolAuth}://{self.destinationIPAuth}:{self.destinationPortAuth}' + "/logout"
            else:
                if request.path.decode("utf-8") == "/login":
                    targer_url = f'{self.destinationProtocol}://{self.destinationIPAuth}:{self.destinationPort}'
                else:
                    authenticated = True
                    targer_url = f'{self.destinationProtocol}://{self.destinationIP}:{self.destinationPort}' + request.path.decode("utf-8")
            
        path = SLASH if not request.path else request.path
        if request.method.decode("utf-8") == 'GET':
            req = requests.get(targer_url, allow_redirects=False, headers=tupelToDicts(request.headers))
        elif  request.method.decode("utf-8") == 'POST':
            req = requests.post(targer_url, headers=tupelToDicts(request.headers), allow_redirects=False, data = request.body)
        else:
            self.client.queue(
                memoryview(
                        build_http_response(
                            405,
                            reason='Method Not Allowed'.encode(),
                            body='Method Not Allowed'.encode(),
                            conn_close=True
                        )
                )
            )
        if req.status_code == 200:
            new_headers = {}
            for key in req.headers:
                if authenticated:
                    stringToreplace = '<body'
                    try:
                        for ch in req.text.split(stringToreplace)[1]:
                            if ch == '>':
                                stringToreplace = stringToreplace + '>'
                                break
                            stringToreplace = stringToreplace + ch
                        request_response = req.content.replace(stringToreplace.encode('utf-8'), stringToreplace.encode('utf-8')+b'<div style="background-color:LightYellow;"><a href="/logout" style="color:blue;text-align:right; float: right;" >Logoff</a><br></div>')
                    except IndexError:
                       request_response = req.content 
                else:
                    request_response = req.content
                new_headers.update({
                    key.encode("utf-8"): req.headers[key].encode("utf-8"),
                })
            self.client.queue(
                okResponse(request_response,
                           headers=new_headers
                           ),
            )
        else:
            new_headers = {}
            for key in req.headers:
                #print(req.headers[key])
                new_headers.update({
                    key.encode("utf-8"): req.headers[key].encode("utf-8"),
                })
            self.client.queue(
                memoryview(
                        build_http_response(
                            req.status_code,
                            reason=http_responses[req.status_code].encode(),
                            body=req.content,
                            headers=new_headers,
                            conn_close=True
                        )
                )
            )

    def on_websocket_message(self, frame: WebsocketFrame) -> None:
        """Open chrome devtools and try using following commands:

        Example:

            ws = new WebSocket("ws://localhost:8899/ws-route-example")
            ws.onmessage = function(m) { console.log(m); }
            ws.send('hello')

        """
        self.client.queue(memoryview(WebsocketFrame.text(frame.data or b'')))
