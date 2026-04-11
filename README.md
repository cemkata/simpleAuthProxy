# simpleAuthProxy

I needed a way to protect with authentication few old projects.
After search I did not found a way and I created my authentication proxy.
The proxy checks if the user is logged and process the request.
It is not the preriest but works.
How it works:

And the authentication is handled by flask application.
For the moment all comunication is based on HTTP requests.

To add users use the Tinkler gui application. The task requested manual control of the ussers.

The configuration consist of:

authentication_server ip -- address of the protected web server

authentication_server port -- port of the protected web server

authentication_server protocol -- http/https

authentication_server auth_username -- authenticate the proxy to auth server

authentication_server auth_password -- authenticate the proxy to auth server

authentication_server sessions users_db -- database holding the users

authentication_server sessions sessionsSecret -- key to encrypt the session

authentication_server sessions sessionsDuration -- duration in days

authentication_server sessions customMsg -- login messege

proxy_server ip -- address of the protected web server
proxy_server port -- port of the protected web server

proxy_server protocol -- http/https

proxy_server startup_retries -- before statr the proxy will try to connect to the auth server for x time

proxy_server waiting_time -- time before next retry

proxy_server destination_server ip -- address of the end web server

proxy_server destination_server port -- port of the protected web server

proxy_server destination_server protocol -- http/https
