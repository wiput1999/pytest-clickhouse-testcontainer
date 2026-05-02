from __future__ import annotations

from datetime import datetime

from clickhouse_driver import Client


def test_insert_and_query(clickhouse_client: Client) -> None:
    clickhouse_client.execute(
        """
        CREATE TABLE events (
            id   UInt64,
            name String,
            ts   DateTime
        ) ENGINE = MergeTree ORDER BY id
        """
    )

    rows = [
        (1, "alpha", datetime(2026, 1, 1, 0, 0, 0)),
        (2, "beta", datetime(2026, 1, 2, 12, 30, 0)),
    ]
    clickhouse_client.execute("INSERT INTO events (id, name, ts) VALUES", rows)

    result = clickhouse_client.execute("SELECT id, name FROM events ORDER BY id")
    assert result == [(1, "alpha"), (2, "beta")]


def test_server_version(clickhouse_client: Client) -> None:
    [(version,)] = clickhouse_client.execute("SELECT version()")
    assert isinstance(version, str)
    assert version.split(".")[0].isdigit()
