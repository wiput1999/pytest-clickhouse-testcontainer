from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from clickhouse_driver import Client


def test_aggregations(clickhouse_client: Client) -> None:
    clickhouse_client.execute(
        "CREATE TABLE sales (category String, amount UInt32) "
        "ENGINE = MergeTree ORDER BY category"
    )
    clickhouse_client.execute(
        "INSERT INTO sales (category, amount) VALUES",
        [
            ("books", 10),
            ("books", 25),
            ("food", 7),
            ("food", 13),
            ("food", 5),
        ],
    )
    result = clickhouse_client.execute(
        "SELECT category, count(), sum(amount) "
        "FROM sales GROUP BY category ORDER BY category"
    )
    assert result == [("books", 2, 35), ("food", 3, 25)]


def test_array_column(clickhouse_client: Client) -> None:
    clickhouse_client.execute(
        "CREATE TABLE posts (id UInt32, tags Array(String)) "
        "ENGINE = MergeTree ORDER BY id"
    )
    clickhouse_client.execute(
        "INSERT INTO posts (id, tags) VALUES",
        [
            (1, ["python", "clickhouse"]),
            (2, ["python", "pytest"]),
            (3, ["rust"]),
        ],
    )

    [(py_count,)] = clickhouse_client.execute(
        "SELECT count() FROM posts WHERE has(tags, 'python')"
    )
    assert py_count == 2

    flat = clickhouse_client.execute(
        "SELECT tag, count() FROM posts "
        "ARRAY JOIN tags AS tag GROUP BY tag ORDER BY tag"
    )
    assert flat == [("clickhouse", 1), ("pytest", 1), ("python", 2), ("rust", 1)]


def test_materialized_view(clickhouse_client: Client) -> None:
    clickhouse_client.execute(
        "CREATE TABLE events (user_id UInt32, ts DateTime) "
        "ENGINE = MergeTree ORDER BY ts"
    )
    clickhouse_client.execute(
        """
        CREATE MATERIALIZED VIEW events_per_user
        ENGINE = SummingMergeTree
        ORDER BY user_id
        AS SELECT user_id, count() AS hits FROM events GROUP BY user_id
        """
    )
    clickhouse_client.execute(
        "INSERT INTO events (user_id, ts) VALUES",
        [
            (1, datetime(2026, 1, 1)),
            (1, datetime(2026, 1, 2)),
            (2, datetime(2026, 1, 1)),
            (1, datetime(2026, 1, 3)),
        ],
    )
    result = clickhouse_client.execute(
        "SELECT user_id, sum(hits) FROM events_per_user "
        "GROUP BY user_id ORDER BY user_id"
    )
    assert result == [(1, 3), (2, 1)]


def test_replacing_merge_tree_final(clickhouse_client: Client) -> None:
    clickhouse_client.execute(
        """
        CREATE TABLE users (id UInt32, name String, version UInt32)
        ENGINE = ReplacingMergeTree(version)
        ORDER BY id
        """
    )
    clickhouse_client.execute(
        "INSERT INTO users (id, name, version) VALUES",
        [
            (1, "alice", 1),
            (1, "alice-renamed", 2),
            (2, "bob", 1),
        ],
    )
    result = clickhouse_client.execute(
        "SELECT id, name FROM users FINAL ORDER BY id"
    )
    assert result == [(1, "alice-renamed"), (2, "bob")]


def test_window_function_running_total(clickhouse_client: Client) -> None:
    clickhouse_client.execute(
        "CREATE TABLE orders (user_id UInt32, ts DateTime, amount UInt32) "
        "ENGINE = MergeTree ORDER BY (user_id, ts)"
    )
    clickhouse_client.execute(
        "INSERT INTO orders (user_id, ts, amount) VALUES",
        [
            (1, datetime(2026, 1, 1), 10),
            (1, datetime(2026, 1, 2), 20),
            (1, datetime(2026, 1, 3), 30),
            (2, datetime(2026, 1, 1), 5),
            (2, datetime(2026, 1, 2), 7),
        ],
    )
    result = clickhouse_client.execute(
        """
        SELECT user_id, amount,
               sum(amount) OVER (PARTITION BY user_id ORDER BY ts) AS running_total
        FROM orders
        ORDER BY user_id, ts
        """
    )
    assert result == [
        (1, 10, 10),
        (1, 20, 30),
        (1, 30, 60),
        (2, 5, 5),
        (2, 7, 12),
    ]


def test_alter_add_column(clickhouse_client: Client) -> None:
    clickhouse_client.execute(
        "CREATE TABLE products (id UInt32, name String) "
        "ENGINE = MergeTree ORDER BY id"
    )
    clickhouse_client.execute(
        "INSERT INTO products (id, name) VALUES", [(1, "widget")]
    )
    clickhouse_client.execute(
        "ALTER TABLE products ADD COLUMN price Decimal(10, 2) DEFAULT 0"
    )
    result = clickhouse_client.execute(
        "SELECT id, name, price FROM products ORDER BY id"
    )
    assert result == [(1, "widget", Decimal("0"))]
