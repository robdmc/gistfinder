import os
import json
import requests
import inspect
import datetime
import re
from dateutil.parser import parse

from .config import Config
from .utils import cached_property


CONFIG_DIR = os.path.realpath(os.path.expanduser('~/.gistfinder'))


class Field:
    def __init__(self, field_name, *keys, transformer=None):
        self._field_name = field_name
        self._keys = keys
        self._transformer = transformer

    def _validate_instance(self, instance):
        required_atts = ['_blob']
        for att_name in required_atts:
            if not hasattr(instance, att_name):
                raise ValueError(f'Fields can only be set on objects having a {att_name} attribute')

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            # Make sure the instance has the required attributes
            self._validate_instance(instance)
            return self.extract(instance)

    def extract(self, instance):
        # Start with val being equal to the blob
        val = instance._blob

        # For each key dig one level deeper into the dict hierarchy
        for key in self._keys:
            val = val[key]

        if self._transformer:
            val = self._transformer(val)

        # This is the desired value
        return val

    def __set__(self, instance, value):
        raise RuntimeError('You cannot set this attribute')


class Blob:
    def __init__(self, blob):
        self._blob = blob

    def to_dict(self, *keys):
        out = {}
        if keys:
            for key in keys:
                out[key] = getattr(self, key)
        else:
            # This will loop over all field attributes
            for member_name, member_object in inspect.getmembers(self.__class__):
                if isinstance(member_object, Field):
                    out[member_name] = getattr(self, member_name)
        return out


class GithubBase:
    BASE_URL = 'https://api.github.com/gists'
    USER_URL = 'https://api.github.com/users/robdmc/gists'
    REX_NEXT = re.compile(r'.*<(https.*?)>; rel="next"')
    PER_PAGE = 99

    def __init__(self):
        self.access_token = os.environ.get('GIST_TOKEN')
        if not self.access_token:
            raise ValueError('You need a github access token')


class ListBlob(Blob):
    gid = Field('gid', 'id')
    description = Field('description', 'description')
    updated_at = Field('updated_at', 'updated_at', transformer=parse)

    def __str__(self):
        return f'{self.__class__.__name__}({self.gid!r})'

    def __repr__(self):
        return self.__str__()


class AllGistGetter(GithubBase):
    def extract_next_link(self, resp):
        link_text = resp.headers.get('link')
        if link_text is not None:
            m = self.REX_NEXT.match(link_text)
            if m:
                return m.group(1)

    def process_response(self, resp, blobs):
        # This is just for debugging
        self.most_recent_resp = resp

        # Load the response into a data dict
        data = json.loads(resp.text)

        # Extract blobs from the data
        blobs.extend([ListBlob(rec) for rec in data])

        # Get the next page link if it exists
        next_link = self.extract_next_link(resp)

        return next_link, blobs

    @property
    def gist_list(self):
        # Initalize to empty blobs
        blobs = []

        # Get the first response
        params = {
            'access_token': self.access_token,
            'per_page': self.PER_PAGE,
            'page': 1
        }
        resp = requests.get(self.USER_URL, params=params)

        # Process the first response
        next_link, blobs = self.process_response(resp, blobs)

        # Process additional pages
        while next_link is not None:
            resp = requests.get(next_link)
            next_link, blobs = self.process_response(resp, blobs)

        return blobs

    @property
    def records(self):
        recs = sorted(self.gist_list, key=lambda r: r.gid)
        return [r.to_dict() for r in recs]


class GistBlob(Blob):
    gid = Field('gid', 'id')
    url = Field('url', 'html_url')
    description = Field('description', 'description')
    files = Field('files', 'files')
    updated_at = Field('updated_at', 'updated_at', transformer=parse)

    def __str__(self):
        return f'{self.__class__.__name__}({self.gid!r})'

    def __repr__(self):
        return self.__str__()


class FileBlob(Blob):
    file_name = Field('file_name', 'filename')
    language = Field('language', 'language')
    raw_url = Field('raw_url', 'raw_url')
    code = Field('code', 'content')

    def __init__(self, blob, gist_id):
        super().__init__(blob)
        self.gid = gist_id

    def __str__(self):
        return f'{self.__class__.__name__}({self.file_name!r})'

    def __repr__(self):
        return self.__str__()


class SingleGistGetter(GithubBase):
    def get_gists(self, gids):
        # Initalize to empty blobs
        blobs = []

        # Get the first response
        params = {
            'access_token': self.access_token,
        }
        for gid in gids:
            url = os.path.join(self.BASE_URL, gid)
            resp = requests.get(url, params=params)
            data = json.loads(resp.text)
            blobs.append(GistBlob(data))
        return blobs


class Updater(Config):
    config_dir = CONFIG_DIR
    db_file = os.path.join(config_dir, 'database.sqlite')
    db_url = f'sqlite:///{db_file}'

    LIST_TABLE = 'list'
    LAST_UPDATE_TABLE = 'last_update'
    GIST_TABLE = 'gist'

    def __init__(self):
        # Make sure the config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

    def sync_lists(self, db):
        table = self.db[self.LIST_TABLE]
        table.drop()
        agc = AllGistGetter()
        recs = agc.records
        for rec in recs:
            table.upsert(rec, ['gid'])

    def sync_last_update(self, db):
        table = db[self.LAST_UPDATE_TABLE]
        table.drop()
        table.insert({'time': datetime.datetime.utcnow()})

    @cached_property
    def unsynced_gist_blobs(self):

        # Get gist ids that need upserting
        recs = list(self.list_table)
        gids = [r['gid'] for r in recs]

        #
        sgg = SingleGistGetter()
        return sgg.get_gists(gids)

    @property
    def unsynced_gist_records(self):
        return [
            r.to_dict('gid', 'url', 'description', 'updated_at')
            for r in self.unsynced_gist_blobs
        ]

    @property
    def unsynced_gist_file_blobs(self):
        blobs = []
        for gist_blob in self.unsynced_gist_blobs:
            for file_data in gist_blob.files.values():
                file_blob = FileBlob(file_data, gist_blob.gid)
                blobs.append(file_blob)
        return blobs

    @property
    def unsynced_gist_file_records(self):
        recs = [
            b.to_dict('gid', 'code', 'file_name', 'language', 'raw_url')
            for b in self.unsynced_gist_file_blobs
        ]
        return recs

    def sync_gists(self, db):
        recs = self.unsynced_gist_file_records
        table = db[self.GIST_TABLE]
        for rec in recs:
            table.upsert(rec, ['gid'], types={'code': db.types.text})

    def sync(self):
        with self.db as db:
            self.sync_lists(db)

            self.sync_gists(db)

            self.sync_last_update(db)
