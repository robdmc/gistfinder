from collections import OrderedDict
from fnmatch import fnmatch
from fuzzywuzzy import process
from .config import Config
from .utils import cached_property


class Loader(Config):
    @cached_property
    def records(self):
        cursor = self.db.query(
            """
                select
                    l.gid,
                    l.description,
                    g.file_name,
                    g.code
                from
                    list as l
                join
                    gist as g
                on
                    g.gid = l.gid
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
        tups = process.extract(expr, records, limit=(len(records) + 1))
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
        if glob_expr:
            records = self.filter_glob(glob_expr, records)

        if text_expr:
            records = self.rank(records, text_expr, 'text')

        if desc_expr:
            records = self.rank(records, desc_expr, 'description')

        if file_expr:
            records = self.rank(records, file_expr, 'file_name')

        if code_expr:
            records = self.rank(records, code_expr, 'code')

        return records









