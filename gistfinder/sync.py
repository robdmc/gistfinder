import os
import requests
import math
import time
from tqdm import tqdm
import sys
from .config import Config


class Updater(Config):
    PER_PAGE = 99
    MAX_GISTS = 10_000

    def blob_generator(self):
        for page in range(int(math.ceil(self.MAX_GISTS / self.PER_PAGE))):
            params = {
                'per_page': self.PER_PAGE,
                'page': page,
            }
            headers = {
                'Authorization': f'token {self.github_token}',
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

    def get_parsed_blob_list(self):
        keys = [
            'url',
            'id',
            'description',
            'created_at',
            'updated_at',

        ]
        records = []

        for item in self.get_list():
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

    def update_list_table(self):
        recs = self.get_parsed_blob_list()
        table = self.list_table
        table.drop()
        table.insert_many(recs)
        table.create_index(['file_url'])

    def get_lookup_dict(self, table):
        return {r['file_url']: r for r in table.all()}

    def get_code(self, url):
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f'Problem retrieving {url}', file=sys.stderr)
            return None

    def update_code_table(self, verbose=True):
        #import pdb; pdb.set_trace()
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
        print('\nSync Complete!', file=sys.stderr)
