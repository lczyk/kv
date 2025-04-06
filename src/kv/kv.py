import argparse
import json
import sqlite3
import sys
from collections.abc import MutableMapping
from contextlib import contextmanager


class KV(MutableMapping):
    def __init__(self, db_uri=":memory:", table="data", timeout=5):
        self._db = sqlite3.connect(db_uri, timeout=timeout)
        self._db.isolation_level = None
        self._table = table
        self._execute(f"CREATE TABLE IF NOT EXISTS {self._table} (key PRIMARY KEY, value)")
        self._locks = 0

    def _execute(self, *args):
        return self._db.cursor().execute(*args)

    def __len__(self):
        [[n]] = self._execute(f"SELECT COUNT(*) FROM {self._table}")
        return n

    def __getitem__(self, key):
        if key is None:
            q = (f"SELECT value FROM {self._table} WHERE key is NULL", ())
        else:
            q = (f"SELECT value FROM {self._table} WHERE key=?", (key,))
        for row in self._execute(*q):
            return json.loads(row[0])
        else:
            raise KeyError

    def __iter__(self):
        return (key for [key] in self._execute(f"SELECT key FROM {self._table}"))

    def __setitem__(self, key, value):
        jvalue = json.dumps(value)
        with self.lock():
            try:
                self._execute(f"INSERT INTO {self._table} VALUES (?, ?)", (key, jvalue))
            except sqlite3.IntegrityError:
                self._execute(f"UPDATE {self._table} SET value=? WHERE key=?", (jvalue, key))

    def __delitem__(self, key):
        if key in self:
            self._execute(f"DELETE FROM {self._table} WHERE key=?", (key,))
        else:
            raise KeyError

    @contextmanager
    def lock(self):
        if not self._locks:
            self._execute("BEGIN IMMEDIATE TRANSACTION")
        self._locks += 1
        try:
            yield
        finally:
            self._locks -= 1
            if not self._locks:
                self._execute("COMMIT")


def main(args=None):
    parser = argparse.ArgumentParser(description="Key-value store backed by SQLite.")
    parser.add_argument("db_uri", help="Database filename or URI")
    parser.add_argument("-t", "--table", nargs=1, default="data", help="Table name")
    subparsers = parser.add_subparsers(dest="command")

    parser_get = subparsers.add_parser("get", help="Get the value for a key")
    parser_get.add_argument("key")

    parser_set = subparsers.add_parser("set", help="Set a value for a key")
    parser_set.add_argument("key")
    parser_set.add_argument("value")

    parser_del = subparsers.add_parser("del", help="Delete a key")
    parser_del.add_argument("key")

    opts = parser.parse_args(args)

    if opts.command is None:
        parser.print_help()
        sys.exit(1)

    kv = KV(opts.db_uri, opts.table)
    if opts.command == "get":
        if opts.key not in kv:
            sys.exit(1)
        print(kv[opts.key])
    elif opts.command == "set":
        kv[opts.key] = opts.value
    elif opts.command == "del":
        if opts.key not in kv:
            sys.exit(1)
        del kv[opts.key]


if __name__ == "__main__":
    main()
