class BaseClient:
    def __init__(self, base_url=""):
        pass

    def login_or_create(self, username):
        pass

    def set_token(self, token):
        pass

    def set_username(self, username):
        pass

    def get_or_head_file(self, path, query=None):
        pass

    def get(self, path, query=None):
        pass

    def post(self, path, body=None):
        pass

    def put(self, path, body):
        pass

    def delete(self, path):
        pass

    def upload_post(self, path, data):
        pass
