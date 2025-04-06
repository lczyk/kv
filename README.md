# KV - simple key/value store

<!-- [![test](https://github.com/MarcinKonowalczyk/kv/actions/workflows/test.yml/badge.svg)](https://github.com/MarcinKonowalczyk/kv/actions/workflows/test.yml) -->
[![Single file](https://img.shields.io/badge/single%20file%20-%20purple)](https://raw.githubusercontent.com/MarcinKonowalczyk/kv/main/src/kv/kv.py)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-BSD_2--Clause-blue.svg)](https://opensource.org/licenses/BSD-2-Clause)
![Python versions](https://img.shields.io/badge/python-3.9%20~%203.13-blue)

Upstream of [mgax/kv](https://github.com/mgax/kv).

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

And that's about it. The code_ is really simple.

