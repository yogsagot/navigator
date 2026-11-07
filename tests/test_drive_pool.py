"""``navigator/lib/drives/pool.py``: a waiter is woken by everything that
should wake it -- an item back, a slot freed, a new generation, the end --
and never sleeps past its *wait* without looking."""

from __future__ import annotations

import threading
import time

import pytest

from navigator.lib.drives.pool import Pool, PoolClosed


class Item:
    """Something a pool makes: numbered, so a test can tell which."""

    count = 0

    def __init__(self) -> None:
        Item.count += 1
        self.number = Item.count


def waiter(pool, *, wait=5.0):
    """``pool.take`` on a thread; its answer (or what it raised) in the dict."""
    out: dict = {}

    def run():
        try:
            out["item"] = pool.take(Item, wait=wait)
        except BaseException as error:  # noqa: BLE001 - the test looks at it
            out["error"] = error

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(0.05)  # waiting by now
    assert thread.is_alive()
    return thread, out


def finished(thread):
    thread.join(2)
    return not thread.is_alive()


def test_an_item_given_back_wakes_the_waiter_and_is_its_own():
    pool = Pool(1)
    held = pool.take(Item)
    thread, out = waiter(pool)
    pool.give(held)
    assert finished(thread) and out["item"] is held


def test_a_new_generation_wakes_the_waiter_to_make_one_and_the_old_is_thrown_away():
    pool = Pool(1)
    old = pool.take(Item)
    thread, out = waiter(pool)
    assert pool.reset() == []
    assert finished(thread) and out["item"] is not old
    assert pool.made == 1
    pool.give(old)              # the old connection's, given back late
    assert pool.made == 1       # not counted against the new one
    assert pool.take(Item, wait=0.05) is None  # and not handed out again


def test_one_thrown_away_frees_its_slot_for_the_waiter():
    pool = Pool(1)
    broken = pool.take(Item)
    thread, out = waiter(pool)
    pool.give(broken, discard=True)
    assert finished(thread) and out["item"] is not broken


def test_closing_wakes_every_waiter_with_the_end():
    pool = Pool(1)
    pool.take(Item)
    waiting = [waiter(pool) for _ in range(3)]
    pool.close()
    for thread, out in waiting:
        assert finished(thread) and isinstance(out["error"], PoolClosed)
    with pytest.raises(PoolClosed):
        pool.take(Item)


def test_a_full_pool_answers_none_after_the_wait_so_the_caller_looks_again():
    pool = Pool(1)
    pool.take(Item)
    started = time.monotonic()
    assert pool.take(Item, wait=0.05) is None
    assert time.monotonic() - started < 1


def test_a_make_that_fails_gives_its_slot_back():
    pool = Pool(1)

    def refuse():
        raise OSError("no route to host")

    with pytest.raises(OSError):
        pool.take(refuse)
    assert pool.made == 0
    assert isinstance(pool.take(Item), Item)


def test_free_ones_are_taken_newest_first_and_adopted_ones_count():
    pool = Pool(3)
    first, second = pool.take(Item), pool.take(Item)
    pool.give(first)
    pool.give(second)
    assert pool.take(Item) is second
    made = pool.adopt(Item())
    assert pool.made == 3
    pool.give(made)
    assert pool.take(Item) is made
