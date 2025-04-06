# KV - simple key/value store

[![Single file](https://img.shields.io/badge/single%20file%20-%20purple)](https://raw.githubusercontent.com/MarcinKonowalczyk/kv/master/src/kv/kv.py)
[![test](https://github.com/MarcinKonowalczyk/kv/actions/workflows/test.yml/badge.svg)](https://github.com/MarcinKonowalczyk/kv/actions/workflows/test.yml)
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

There is a locking facility that uses SQLite's transaction API:

```python
>>> with kv.lock():
...   l = db[42]
...   l += ['or is it?']
...   db[42] = l
```

### Install

Just copy the single-module file to your project and import it.

```bash
cp ./src/kv/kv.py src/your_package/_kv.py
```

Or even better, without checking out the repository:

```bash
curl https://raw.githubusercontent.com/MarcinKonowalczyk/kv/master/src/kv/kv.py > src/your_package/_kv.py
```

Note that like this *you take ownership of the code* and you are responsible for keeping it up-to-date. If you change it that's fine (keep the license pls). That's the point here. You can also copy the code to your project and modify it as you wish.

If you want you can also build and install it as a package, but then the source lives somewhere else. That might be what you want though. 🤷‍♀️

```bash
pip install flit
flit build
ls dist/*
pip install dist/*.whl
```
