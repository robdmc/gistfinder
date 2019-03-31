import os
import dataset

CONFIG_DIR = os.path.realpath(os.path.expanduser('~/.gistfinder'))


class Config:
    config_dir = CONFIG_DIR
    db_file = os.path.join(config_dir, 'database.sqlite')
    db_url = f'sqlite:///{db_file}'

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
