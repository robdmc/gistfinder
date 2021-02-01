import os
import sys
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

    def _check_okay(self):
        has_user = False
        has_token = False
        has_auth_file = os.path.isfile(self.auth_file)

        if has_auth_file:
            with open(self.auth_file) as buff:
                blob = json.load(buff)
                if blob.get('GIST_USER'):
                    has_user = True
                if blob.get('GIST_TOKEN'):
                    has_token = True
        
        msg = ''
        if not has_user:
            msg += '\nYou need to set up a user: gistfinder -u <username>\n'

        if not has_token:
            msg += '\nYou need to set up a token: gistfinder -t <access_token>'

        if not has_user and not has_token:
            msg = '\nYou need to set up a user and token: gistfinder -u <username> -t <access_token>'

        if msg:
            print(msg, file=sys.stderr)
            print('\n', file=sys.stdout)
            sys.exit(1)

        

    @cached_property
    def user_url(self):
        self._check_okay()

        with open(self.auth_file) as f:
            user = json.loads(f.read()).get('GIST_USER')

        url = f'https://api.github.com/users/{user}/gists'
        return url

    @cached_property
    def db(self):
        self._check_okay()
        return dataset.connect(url=self.db_url)

    @property
    def list_table(self):
        return self.db[self.LIST_TABLE]

    @property
    def code_table(self):
        return self.db[self.CODE_TABLE]

    @cached_property
    def github_token(self):
        self._check_okay()

        with open(self.auth_file) as f:
            access_token = json.loads(f.read()).get('GIST_TOKEN')

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
