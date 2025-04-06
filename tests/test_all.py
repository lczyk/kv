import os
import sqlite3
from copy import deepcopy
from queue import Queue
from threading import Thread
from typing import Iterator
from unittest import mock

import pytest
from conftest import __tests_dir__

from kv import KV
from kv.kv import main as kv_main


@pytest.fixture
def kv() -> Iterator[KV]:
    kv_file = str(__tests_dir__ / "kv.sqlite")
    kv_instance = KV(kv_file)
    yield kv_instance
    os.remove(kv_file)


def test_new_kv_is_empty(kv: KV) -> None:
    assert len(kv) == 0


def test_kv_with_two_items_has_size_two(kv: KV) -> None:
    kv["a"] = "x"
    kv["b"] = "x"
    assert len(kv) == 2


def test_get_missing_value_raises_key_error(kv: KV) -> None:
    with pytest.raises(KeyError):
        kv["missing"]


def test_get_missing_value_returns_default(kv: KV) -> None:
    assert kv.get("missing") is None


def test_get_missing_value_with_default_returns_argument(kv: KV) -> None:
    fallback = object()
    assert kv.get("missing", fallback) is fallback


def test_contains_missing_value_is_false(kv: KV) -> None:
    assert "missing" not in kv


def test_contains_existing_value_is_true(kv: KV) -> None:
    kv["a"] = "b"
    assert "a" in kv


def test_saved_item_is_retrieved_via_getitem(kv: KV) -> None:
    kv["a"] = "b"
    assert kv["a"] == "b"


def test_saved_item_is_retrieved_via_get(kv: KV) -> None:
    kv["a"] = "b"
    assert kv.get("a") == "b"


def test_updated_item_is_retrieved_via_getitem(kv: KV) -> None:
    kv["a"] = "b"
    kv["a"] = "c"
    assert kv["a"] == "c"


def test_udpate_with_dictionary_items_retrieved_via_getitem(kv: KV) -> None:
    kv.update({"a": "b"})
    assert kv["a"] == "b"


def test_delete_missing_item_raises_key_error(kv: KV) -> None:
    with pytest.raises(KeyError):
        del kv["missing"]


def test_get_deleted_item_raises_key_error(kv: KV) -> None:
    kv["a"] = "b"
    del kv["a"]
    with pytest.raises(KeyError):
        kv["a"]


def test_iter_yields_keys(kv: KV) -> None:
    kv["a"] = "x"
    kv["b"] = "x"
    kv["c"] = "x"
    assert set(kv) == {"a", "b", "c"}


def test_value_saved_with_int_key_is_retrieved_with_int_key(kv: KV) -> None:
    kv[13] = "a"
    assert kv.get(13) == "a"


def test_value_saved_with_int_key_is_not_retrieved_with_str_key(kv: KV) -> None:
    kv[13] = "a"
    assert kv.get("13") is None


def test_value_saved_with_str_key_is_not_retrieved_with_int_key(kv: KV) -> None:
    kv["13"] = "a"
    assert kv.get(13) is None


def test_value_saved_at_null_key_is_retrieved(kv: KV) -> None:
    kv[None] = "a"
    assert kv.get(None) == "a"


def test_value_saved_with_float_key_is_retrieved_with_float_key(kv: KV) -> None:
    kv[3.14] = "a"
    assert kv.get(3.14) == "a"


def test_value_saved_with_unicode_key_is_retrieved(kv: KV) -> None:
    key = "\u2022"
    kv[key] = "a"
    assert kv.get(key) == "a"


################################################################################


def test_value_saved_by_one_kv_client_is_read_by_another() -> None:
    kv1 = KV(__tests_dir__ / "kv.sqlite")
    kv1["a"] = "b"
    kv2 = KV(__tests_dir__ / "kv.sqlite")
    assert kv2["a"] == "b"


def test_deep_structure_is_retrieved_the_same() -> None:
    value = {"a": ["b", {"c": 123}]}
    kv1 = KV(__tests_dir__ / "kv.sqlite")
    kv1["a"] = deepcopy(value)
    kv2 = KV(__tests_dir__ / "kv.sqlite")
    assert kv2["a"] == value


def test_lock_fails_if_db_already_locked() -> None:
    db_path = __tests_dir__ / "kv.sqlite"
    q1: Queue[None] = Queue()
    q2: Queue[None] = Queue()
    kv2 = KV(db_path, timeout=0.1)

    def locker() -> None:
        kv1 = KV(db_path)
        with kv1.lock():
            q1.put(None)
            q2.get()

    th = Thread(target=locker)
    th.start()
    try:
        q1.get()
        # with self.assertRaises(sqlite3.OperationalError) as cm1, kv2.lock():
        # pass
        with (
            pytest.raises(sqlite3.OperationalError, match="database is locked"),
            kv2.lock(),
        ):
            pass
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            kv2["a"] = "b"
    finally:
        q2.put(None)
        th.join()


def test_lock_during_lock_still_saves_value() -> None:
    kv1 = KV(__tests_dir__ / "kv.sqlite")
    with kv1.lock(), kv1.lock():
        kv1["a"] = "b"
    assert kv1.get("a") == "b"


def test_same_database_can_contain_two_namespaces() -> None:
    kv1 = KV(__tests_dir__ / "kv.sqlite")
    kv2 = KV(__tests_dir__ / "kv.sqlite", table="other")
    kv1["a"] = "b"
    kv2["a"] = "c"
    assert kv1.get("a") == "b"
    assert kv2.get("a") == "c"


################################################################################


def _run(db: str, /, *args: str) -> tuple[int, str]:
    with (
        mock.patch("kv.kv.print") as mprint,
        mock.patch("sys.stderr") as mstderr,
    ):
        mstderr.write = mprint
        retcode: int = 0
        output = ""
        try:
            kv_main(args=(db, *args))
        except SystemExit as e:
            retcode = e.code if isinstance(e.code, int) else -1
        if mprint.called:
            output = mprint.call_args[0][0]
        return retcode, output


def test_cli_get(kv: KV) -> None:
    assert "foo" not in kv
    assert _run(kv.db_uri, "get", "foo") == (1, "")
    kv["foo"] = "test"
    assert "foo" in kv
    assert _run(kv.db_uri, "get", "foo") == (0, "test")


def test_cli_set(kv: KV) -> None:
    assert "foo" not in kv
    assert _run(kv.db_uri, "set", "foo", "test") == (0, "")
    assert "foo" in kv
    assert kv["foo"] == "test"


def test_cli_del(kv: KV) -> None:
    assert "foo" not in kv
    assert _run(kv.db_uri, "del", "foo") == (1, "")
    kv["foo"] = "test"
    assert "foo" in kv
    assert _run(kv.db_uri, "del", "foo") == (0, "")
    assert "foo" not in kv
