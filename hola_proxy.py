#-*- coding:utf-8 -*-
import urllib2
import json
import time
from geoip import geolite2
from requests.auth import HTTPProxyAuth

class HolaProxy():

    def __init__(self, username, password, session, country=None, dns=None, servercountry=None):
        self.base = 1
        self.usename = username
        self.password = password
        self.session = session
        self.country = country
        self.dns = dns
        self.servercountry = servercountry
        self.generate_proxy()

    def generate_proxy_auth(self):
        username = ''
        username_prifix = 'lum-customer-%s-zone-gen' % self.username
        username += username_prifix
        if self.country:
            username += '-country-%s' % self.country
        if self.dns:
            username += '-dns-%s' % self.dns
        proxy_session_tag = 'sid%s_%s' % (self.session, self.base)
        username += '-session-%s' % proxy_session_tag
        authentication_code = self.password
        self.proxy_auth = HTTPProxyAuth(username, authentication_code)

    def generate_proxy(self):
        self.generate_proxy_auth()
        hola_proxy_suffix = '45.55.206.5:22225'
        proxy = ''
        if self.servercountry:
            proxy += 'servercountry-%s.' % self.servercountry
        self.proxy = 'http://' + proxy + hola_proxy_suffix
        
    def refresh(self):
        self.base += 1
        self.generate_proxy()
        
    @property    
    def remote(self):
        return self.proxy

    def ping(self):
        opener = urllib2.build_opener(urllib2.ProxyHandler({'http': self.remote}))
        try:
            t0 = time.time()
            req = urllib2.Request('http://lumtest.com/myip')
            r = opener.open(req, timeout=10)
            ip = r.read().strip()
            match = geolite2.lookup(ip)
            ttl = time.time() - t0
            r.close()
            return {
                'status': 'ok', 
                'result': {
                    'ip': ip, 
                    'ttl': ttl,
                    'country': match.country,
                    'str': self.remote
                }
            }
        except Exception, e:
            return {'status': 'error', 'result': repr(e), 'proxy': str(self.remote)}

if __name__ == '__main__':
    import threading
    stats = {}
    def test_hola(th):
        session = th

        proxy = HolaProxy(session, country='cn')
        for i in range(100):
            ping_resp = proxy.ping()
            if ping_resp['status'] == 'ok':
                if ping_resp['result']['ip'] not in stats:
                    stats[ping_resp['result']['ip']] = set()
                stats[ping_resp['result']['ip']].add(th)
    threads = []
    for th in range(10):
        t = threading.Thread(target=test_hola, args=(th,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

