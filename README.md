# simpleAuthProxy

I needed a way to protect with authentication few old projects.
After search I did not found a way and I created my authentication proxy.
The proxy checks if the user is logged and process the request.
It is not the preriest but works.
How it works:
I use the proxy.py library.

And the authentication is handled by flask application.
For the moment all comunication is based on HTTP requests.

To add users use the Tinkler gui application. The task requested manual control of the ussers.

The configuration consist of:
target ip of the protected web page
target port of the protected web page
target protocol http/https
Ip of the flask authenticator
Port of the flask authenticator
Protocol http/https of flask authenticator
Adress where the proxy will listen
Port where the proxy will listen
User db file (sqlite database)
Duration of the sessions
