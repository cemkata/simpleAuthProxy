import multiprocessing

import login_app
import proxy

def start_auth_server():
    login_app.start()

def start_proxy():
    proxy.start()
	
if __name__ == '__main__':
    p_auth = multiprocessing.Process(name='auth_server', target=start_auth_server)
    p_proxy = multiprocessing.Process(name='proxy', target=start_proxy)
    p_auth.start()
    p_proxy.start()