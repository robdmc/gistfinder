import os
import dataset
import json

CONFIG_DIR = os.path.realpath(os.path.expanduser('~/.gistfinder'))


class Config:
    config_dir = CONFIG_DIR
    db_file = os.path.join(config_dir, 'database.sqlite')
    auth_file = os.path.join(config_dir, 'github_auth.json')

    db_url = 'sqlite:///{db_file}'.format(db_file=db_file)

    LIST_TABLE = 'list'
    LAST_UPDATE_TABLE = 'last_update'
    GIST_TABLE = 'gist'

    @property
    def db(self):
        return dataset.connect(url=self.db_url)

    @property
    def list_table(self):
        return self.db[self.LIST_TABLE]

    @property
    def gist_table(self):
        return self.db[self.GIST_TABLE]

    @property
    def github_token(self):
        with open(self.auth_file) as f:
            access_token = json.loads(f.read()).get('GIST_TOKEN')

        if not access_token:
            raise ValueError('You need to set up a github access token')
        return access_token

    def set_github_token(self, token):
        blob = {'GIST_TOKEN': token}
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.auth_file, 'w') as out_file:
            json.dump(blob, out_file)

        print()
        print('Wrote credentials to: {}'.format(self.auth_file))
        print()

