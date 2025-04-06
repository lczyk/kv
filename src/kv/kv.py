"""
Single-file moduel with a simple key/value store.

KV provides a dictionary-like interface on top of SQLite. Keys can be
unicode strings, numbers or None. Values are stored as JSON.

```python
>>> from kv import KV
>>> db = KV('/tmp/demo.kv')
>>> db['hello'] = 'world'
>>> db[42] = ['answer', 2, {'ultimate': 'question'}]
>>> dict(db)
{42: [u'answer', 2, {u'ultimate': u'question'}], u'hello': u'world'}
```

There is a locking facility that uses SQLite's transaction API::

```python
>>> with kv.lock():
...   l = db[42]
...   l += ['or is it?']
...   db[42] = l
```

Original version written by Alex Morega, 2012-2025 (until 0.4.1).
Adapted to single-file-module by Marcin Konowalczyk, 2024 (0.5.0+).
"""

import argparse
import json
import sqlite3
import sys
from collections.abc import MutableMapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Union

if TYPE_CHECKING:
    from typing_extensions import override
else:
    override = lambda x: x  # noqa: E731

__version__ = "0.5.0"

__all__ = ["KV"]


class KV(MutableMapping):
    def __init__(
        self,
        db_uri: Union[str, Path] = ":memory:",
        table: str = "data",
        timeout: float = 5.0,
    ) -> None:
        self._db_uri = str(db_uri)
        self._db = sqlite3.connect(self._db_uri, timeout=timeout)
        self._db.isolation_level = None
        self._table = table
        self._execute(f"CREATE TABLE IF NOT EXISTS {self._table} (key PRIMARY KEY, value)")
        self._locks = 0

    @property
    def db_uri(self) -> str:
        return self._db_uri

    def _execute(self, sql: str, *args: Any) -> sqlite3.Cursor:
        return self._db.cursor().execute(sql, *args)

    @override
    def __len__(self) -> int:
        [[n]] = self._execute(f"SELECT COUNT(*) FROM {self._table}")
        return n  # type: ignore[no-any-return]

    @override
    def __getitem__(self, key: Union[str, None]) -> Any:
        q: tuple[str, tuple[Any, ...]]
        if key is None:
            q = (f"SELECT value FROM {self._table} WHERE key is NULL", ())
        else:
            q = (f"SELECT value FROM {self._table} WHERE key=?", (key,))
        for row in self._execute(*q):
            return json.loads(row[0])
        else:
            raise KeyError

    @override
    def __iter__(self) -> Iterator[str]:
        return (key for [key] in self._execute(f"SELECT key FROM {self._table}"))

    @override
    def __setitem__(self, key: Union[str, None], value: Any) -> None:
        jvalue = json.dumps(value)
        with self.lock():
            try:
                self._execute(f"INSERT INTO {self._table} VALUES (?, ?)", (key, jvalue))
            except sqlite3.IntegrityError:
                self._execute(f"UPDATE {self._table} SET value=? WHERE key=?", (jvalue, key))

    @override
    def __delitem__(self, key: Union[str, None]) -> None:
        if key in self:
            self._execute(f"DELETE FROM {self._table} WHERE key=?", (key,))
        else:
            raise KeyError

    @contextmanager
    def lock(self) -> Iterator[None]:
        if not self._locks:
            self._execute("BEGIN IMMEDIATE TRANSACTION")
        self._locks += 1
        try:
            yield
        finally:
            self._locks -= 1
            if not self._locks:
                self._execute("COMMIT")


def main(args: Union[list[str], None] = None) -> None:
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


__license__ = """
Copyright 2012-2025 Alex Morega
Copyright 2024 Marcin Konowalczyk
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

if __name__ == "__main__":
    main()
