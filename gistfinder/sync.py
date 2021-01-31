import os
import requests
import math
import time
import tqdm
import sys
from .config import Config


class Updater(Config):
    PER_PAGE = 99
    MAX_GISTS = 10_000

    def __init__(self):
        self.access_token = os.environ['GIST_TOKEN']

    def blob_generator(self):
        for page in range(int(math.ceil(self.MAX_GISTS / self.PER_PAGE))):
            params = {
                'per_page': self.PER_PAGE,
                'page': page,
            }
            headers = {
                'Authorization': f'token {self.access_token}',
                'accept': 'application/vnd.github.v3+json'
            }
            resp = requests.get(self.user_url, params=params, headers=headers)
            self.latest_resp = resp
            blobs = resp.json()
            if blobs:
                yield blobs
            else:
                break

    def get_list(self):
        rec_list = []
        for ll in self.blob_generator():
            rec_list.extend(ll)

        return rec_list

    # @ezr.pickle_cached_container()
    # def ll(self):
    #     return self.get_list()

    def get_parsed_blob_list(self):
        keys = [
            'url',
            'id',
            'description',
            'created_at',
            'updated_at',

        ]
        records = []

        #for item in self.get_list(): TODO
        for item in self.get_list()[:3]:
            record_template = {k: item[k] for k in keys}
            for file in item['files'].values():
                record = record_template.copy()
                record['file'] = file['filename']
                record['language'] = file.get('language', 'unkown')
                record['file_url'] = file['raw_url']
                record['size'] = file.get('size', 0)
                record['gist_id'] = record.pop('id')
                records.append(record)

        dedup = {r['file_url']: r for r in records}
        records = list(dedup.values())
        records = [r for r in records if not r['file'].endswith('ipynb')]

        return records

    def update_list_table(self, recs, print=False):
        table = self.list_table
        table.drop()
        table.insert_many(recs)
        table.create_index(['file_url'])

    def get_lookup_dict(self, table):
        return {r['file_url']: r for r in self.list_table.all()}

    def get_code(self, url):
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f'Problem retrieving {url}', file=sys.stderr)
            return None

    def update_code_table(self, verbose=True):
        list_table = self.list_table
        code_table = self.code_table

        code_lookup = self.get_lookup_dict(code_table)
        list_lookup = self.get_lookup_dict(list_table)

        missing_file_urls = set(list_lookup.keys()) - set(code_lookup.keys())
        deleted_file_urls = set(code_lookup.keys()) - set(list_lookup.keys())

        code_table.delete(file_url={'in': tuple(deleted_file_urls)})

        if not missing_file_urls:
            return

        if verbose:
            missing_file_urls = tqdm(missing_file_urls)

        for file_url in missing_file_urls:
            code = self.get_code(file_url)
            if code:
                code_table.insert(dict(file_url=file_url, code=code))
                time.sleep(.1)

        code_table.create_index(['file_url'])

    def reset(self):
        if os.path.isfile(self.db_file):
            print('Removing {}'.format(self.db_file), file=sys.stderr)
            os.unlink(self.db_file)
        self.sync()

    def sync(self):
        self.update_list_table()
        self.update_code_table()
        # self.u
        # with self.db as db:
        #     self.sync_lists(db)

        #     self.sync_gists(db)

        #     self.sync_last_update(db)




#####################################################################################################################
#####################################################################################################################
#####################################################################################################################
#####################################################################################################################
# import os
# import json
# import sys

# import requests
# import inspect
# import datetime
# import re
# from dateutil.parser import parse
# import pytz


# from .config import Config
# from .utils import cached_property


# # CONFIG_DIR = os.path.realpath(os.path.expanduser('~/.gistfinder'))
# UTC = pytz.timezone('utc')


# class Field:
#     def __init__(self, field_name, *keys, transformer=None):
#         self._field_name = field_name
#         self._keys = keys
#         self._transformer = transformer

#     def _validate_instance(self, instance):
#         required_atts = ['_blob']
#         for att_name in required_atts:
#             if not hasattr(instance, att_name):
#                 raise ValueError(
#                     'Fields can only be set on objects having a {att_name} attribute'.format(
#                         att_name=att_name
#                     )
#                 )

#     def __get__(self, instance, owner):
#         if instance is None:
#             return self
#         else:
#             # Make sure the instance has the required attributes
#             self._validate_instance(instance)
#             return self.extract(instance)

#     def extract(self, instance):
#         # Start with val being equal to the blob
#         val = instance._blob

#         # For each key dig one level deeper into the dict hierarchy
#         for key in self._keys:
#             val = val[key]

#         if self._transformer:
#             val = self._transformer(val)

#         # This is the desired value
#         return val

#     def __set__(self, instance, value):
#         raise RuntimeError('You cannot set this attribute')


# class Blob:
#     def __init__(self, blob):
#         self._blob = blob

#     def to_dict(self, *keys):
#         out = {}
#         if keys:
#             for key in keys:
#                 out[key] = getattr(self, key)
#         else:
#             # This will loop over all field attributes
#             for member_name, member_object in inspect.getmembers(self.__class__):
#                 if isinstance(member_object, Field):
#                     out[member_name] = getattr(self, member_name)
#         return out


# class GithubBase(Config):
#     BASE_URL = 'https://api.github.com/gists'
#     USER_URL = 'https://api.github.com/users/robdmc/gists'
#     REX_NEXT = re.compile(r'.*<(https.*?)>; rel="next"')
#     PER_PAGE = 99

#     def __init__(self):
#         self.access_token = Config().github_token


# class ListBlob(Blob):
#     gid = Field('gid', 'id')
#     description = Field('description', 'description')
#     updated_at = Field('updated_at', 'updated_at', transformer=parse)

#     def __str__(self):
#         return '{self.__class__.__name__}({gid})'.format(gid=self.gid)

#     def __repr__(self):
#         return self.__str__()


# class AllGistGetter(GithubBase):
#     def extract_next_link(self, resp):
#         link_text = resp.headers.get('link')
#         if link_text is not None:
#             m = self.REX_NEXT.match(link_text)
#             if m:
#                 return m.group(1)

#     def process_response(self, resp, blobs):
#         # This is just for debugging
#         self.most_recent_resp = resp

#         # Load the response into a data dict
#         data = json.loads(resp.text)

#         # Extract blobs from the data
#         blobs.extend([ListBlob(rec) for rec in data])

#         # Get the next page link if it exists
#         next_link = self.extract_next_link(resp)

#         return next_link, blobs

#     @property
#     def gist_list(self):
#         # Initalize to empty blobs
#         blobs = []

#         # Get the first response
#         params = {
#             'access_token': self.access_token,
#             'per_page': self.PER_PAGE,
#             'page': 1
#         }
#         resp = requests.get(self.USER_URL, params=params)
#         # Process the first response
#         next_link, blobs = self.process_response(resp, blobs)

#         # Process additional pages
#         while next_link is not None:
#             resp = requests.get(next_link)
#             next_link, blobs = self.process_response(resp, blobs)

#         return blobs

#     @property
#     def records(self):
#         recs = sorted(self.gist_list, key=lambda r: r.gid)
#         return [r.to_dict() for r in recs]


# class GistBlob(Blob):
#     gid = Field('gid', 'id')
#     url = Field('url', 'html_url')
#     description = Field('description', 'description')
#     files = Field('files', 'files')
#     updated_at = Field('updated_at', 'updated_at', transformer=parse)

#     def __str__(self):
#         return '{self.__class__.__name__}({gid}})'.format(gid=self.gid)

#     def __repr__(self):
#         return self.__str__()


# class FileBlob(Blob):
#     file_name = Field('file_name', 'filename')
#     language = Field('language', 'language')
#     raw_url = Field('raw_url', 'raw_url')
#     code = Field('code', 'content')

#     def __init__(self, blob, gist_id):
#         super().__init__(blob)
#         self.gid = gist_id

#     def __str__(self):
#         return '{self.__class__.__name__}({file_name})'.format(file_name=self.file_name)

#     def __repr__(self):
#         return self.__str__()


# class SingleGistGetter(GithubBase):
#     def get_gists(self, gids):
#         # Initalize to empty blobs
#         blobs = []

#         # Get the first response
#         params = {
#             'access_token': self.access_token,
#         }
#         total = len(gids)
#         for ind, gid in enumerate(gids):
#             if ind % 5 == 0:
#                 print('Pulling {} of {}'.format(ind + 1, total), file=sys.stderr)
#             url = os.path.join(self.BASE_URL, gid)
#             resp = requests.get(url, params=params)
#             data = json.loads(resp.text)
#             blobs.append(GistBlob(data))
#         print('Done.')
#         return blobs


# class Updater(Config):

#     LIST_TABLE = 'list'
#     LAST_UPDATE_TABLE = 'last_update'
#     GIST_TABLE = 'gist'

#     def __init__(self):
#         # Make sure the config directory exists
#         os.makedirs(self.config_dir, exist_ok=True)

#     def sync_lists(self, db):
#         table = self.db[self.LIST_TABLE]
#         table.drop()
#         agc = AllGistGetter()
#         recs = agc.records

#         for rec in recs:
#             table.upsert(rec, ['gid'])

#     def sync_last_update(self, db):
#         table = db[self.LAST_UPDATE_TABLE]
#         table.drop()
#         now = datetime.datetime.utcnow()
#         now = UTC.localize(now)
#         table.insert({'time': now})

#     @cached_property
#     def last_updated_time(self):
#         table = self.db[self.LAST_UPDATE_TABLE]
#         time_recs = list(table)
#         if not time_recs:
#             min_time = UTC.localize(datetime.datetime(1970, 1, 1))
#             return min_time
#         rec = time_recs[0]
#         time = rec['time']
#         if time.tzinfo is None:
#             time = UTC.localize(time)
#         return time

#     @cached_property
#     def unsynced_gist_blobs(self):
#         # Pull list of all gist meta info
#         agc = AllGistGetter()
#         recs = agc.gist_list

#         # Filter down to those with new update times
#         recs = [r for r in recs if r.updated_at > self.last_updated_time]

#         # Get gist ids that need upserting
#         gids = [r.gid for r in recs]

#         # Sync the gists
#         sgg = SingleGistGetter()
#         return sgg.get_gists(gids)

#     @property
#     def unsynced_gist_records(self):
#         return [
#             r.to_dict('gid', 'url', 'description', 'updated_at')
#             for r in self.unsynced_gist_blobs
#         ]

#     @property
#     def unsynced_gist_file_blobs(self):
#         blobs = []
#         for gist_blob in self.unsynced_gist_blobs:
#             for file_data in gist_blob.files.values():
#                 file_blob = FileBlob(file_data, gist_blob.gid)
#                 blobs.append(file_blob)
#         return blobs

#     @property
#     def unsynced_gist_file_records(self):
#         recs = [
#             b.to_dict('gid', 'code', 'file_name', 'language', 'raw_url')
#             for b in self.unsynced_gist_file_blobs
#         ]
#         return recs

#     def sync_gists(self, db):
#         recs = self.unsynced_gist_file_records
#         if not recs:
#             print('Up to date', file=sys.stderr)
#             print()
#             return

#         table = db[self.GIST_TABLE]
#         for rec in recs:
#             table.upsert(rec, ['gid'], types={'code': db.types.text})

#     def reset(self):
#         config = Config()
#         db_file = config.db_file
#         if os.path.isfile(db_file):
#             print('Removing {}'.format(db_file), file=sys.stderr)
#             os.unlink(db_file)
#         self.sync()

#     def sync(self):
#         with self.db as db:
#             self.sync_lists(db)

#             self.sync_gists(db)

#             self.sync_last_update(db)
