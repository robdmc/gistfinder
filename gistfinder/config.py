import os
import dataset
import json
from .utils import cached_property

CONFIG_DIR = os.path.realpath(os.path.expanduser('~/.config/gistfinder'))


class Config:
    config_dir = CONFIG_DIR
    db_file = os.path.join(config_dir, 'database.sqlite')
    auth_file = os.path.join(config_dir, 'github_auth.json')

    db_url = 'sqlite:///{db_file}'.format(db_file=db_file)

    BASE_URL = 'https://api.github.com/gists'
    LIST_TABLE = 'list_table'
    CODE_TABLE = 'code_table'

    @cached_property
    def user_url(self):
        with open(self.auth_file) as f:
            user = json.loads(f.read()).get('GIST_USER')

        if not user:
            raise ValueError('You need to set up a github user')

        url = f'https://api.github.com/users/{user}/gists'
        return url

    @cached_property
    def db(self):
        return dataset.connect(url=self.db_url)

    @property
    def list_table(self):
        return self.db[self.LIST_TABLE]

    @property
    def code_table(self):
        return self.db[self.CODE_TABLE]

    @cached_property
    def github_token(self):
        with open(self.auth_file) as f:
            access_token = json.loads(f.read()).get('GIST_TOKEN')

        if not access_token:
            raise ValueError('You need to set up a github access token')
        return access_token

    def update(self, **updates):
        blob = {}
        os.makedirs(self.config_dir, exist_ok=True)

        if os.path.isfile(self.auth_file):
            with open(self.auth_file) as buff:
                saved_blob = json.load(buff)
            blob.update(saved_blob)

        blob.update(updates)

        with open(self.auth_file, 'w') as out_file:
            json.dump(blob, out_file)

    def set_github_token(self, token):
        self.update(GIST_TOKEN=token)

    def set_github_user(self, user):
        self.update(GIST_USER=user)
