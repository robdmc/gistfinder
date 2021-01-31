from collections import OrderedDict
from fnmatch import fnmatch
from fuzzywuzzy import process
from .config import Config
from .utils import cached_property


class Loader(Config):
    @cached_property
    def has_tables(self):
        expected_tables = {Config.LIST_TABLE, Config.CODE_TABLE}
        existing_tables = set(self.db.tables)
        return existing_tables.intersection(expected_tables) == expected_tables

    @cached_property
    def records(self):
        if not self.has_tables:
            return OrderedDict()

        cursor = self.db.query(
            f"""
                select
                    l.gist_id AS gid,
                    l.description,
                    l.file AS file_name,
                    c.code
                from
                    {Config.LIST_TABLE} as l
                join
                    {Config.CODE_TABLE} as c
                on
                    c.file_url = l.file_url
                order by
                    file_name collate nocase asc,
                    description asc
            """
        )
        raw_records = list(cursor)

        out_recs = OrderedDict()
        for rec in raw_records:
            rec['text'] = '\n'.join(
                [
                    rec['file_name'],
                    rec['description'],
                    rec['code']
                ]
            )
            out_recs[rec['gid']] = rec
        return out_recs

    def rank(self, records, expr, field):
        search_recs = OrderedDict((t[0], t[1][field]) for t in records.items())
        tups = process.extract(expr, search_recs, limit=len(records) + 1)
        out = OrderedDict()
        for tup in tups:
            gid = tup[2]
            out[gid] = records[gid]
        return out

    def filter_glob(self, expr, records):
        out = OrderedDict()
        for gid, rec in records.items():
            if fnmatch(rec['file_name'], expr):
                out[gid] = rec
        return out

    def get(self, *, glob_expr=None, text_expr=None, desc_expr=None, file_expr=None, code_expr=None):
        records = self.records
        if glob_expr and records:
            records = self.filter_glob(glob_expr, records)

        if text_expr and records:
            records = self.rank(records, text_expr, 'text')

        if desc_expr and records:
            records = self.rank(records, desc_expr, 'description')

        if file_expr and records:
            records = self.rank(records, file_expr, 'file_name')

        if code_expr and records:
            records = self.rank(records, code_expr, 'code')

        return records
