# -*- coding: utf-8 -*-
import proxy
import ipaddress
import json
import os
import requests
import time

if __name__ == '__main__':

  pwd = os.getcwd()
  os.chdir("..")
  with open('config.json', 'r') as file:
    data = json.load(file)
  
  os.chdir(pwd)
  with open('proxy_plugin/web_server_route_template.py', 'r') as file:
    plugin = file.read()

  plugin = plugin.replace("$destinationIPAuth", data['destinationIPAuth'])
  plugin = plugin.replace("$destinationPortAuth", str(data['destinationPortAuth']))
  plugin = plugin.replace("$destinationProtocolAuth", str(data['destinationProtocolAuth']))
  plugin = plugin.replace("$destinationIP", data['destinationIP'])
  plugin = plugin.replace("$destinationPort", str(data['destinationPort']))
  plugin = plugin.replace("$destinationProtocol", str(data['destinationProtocol']))

  with open('proxy_plugin/web_server_route.py', 'w') as f:
    f.write(plugin)
  
  retries = 0
  waitingTime = 0.5
  while True:
      try:
         _ = requests.get(f'{data['destinationProtocolAuth']}://{data['destinationIPAuth']}:{data['destinationPortAuth']}/protected', allow_redirects=False)
         break
      except:
         if retries > 20:
            print("Failed to start after "+str(waitingTime * retries)+" seconds")
            print("And "+str(retries)+" retries!")
            exit(255)
         retries +=1
         time.sleep(waitingTime)

  proxy.main(
    hostname=ipaddress.IPv4Address(data['lsitingIP']),
    port=data['lsitingPort'],
    plugins=['proxy.http.proxy.HttpProxyPlugin', 'proxy.http.server.HttpWebServerPlugin', 'proxy_plugin.WebServerPlugin']
  )