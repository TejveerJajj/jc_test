class Config:
    def __init__(self, username, password, base_url):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.search_url = f"{base_url}.watches/_search?size=10000"
        self.action_url = f"{base_url}_watcher/watch/"
        self.req_headers = {'content-type': 'application/json'}
        self.cert_path = "cert/cert.cert"
