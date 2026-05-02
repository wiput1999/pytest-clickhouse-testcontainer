from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from clickhouse_driver import Client
from testcontainers.clickhouse import ClickHouseContainer

CLICKHOUSE_IMAGE = "clickhouse/clickhouse-server:25.10-alpine"


@pytest.fixture(scope="session")
def clickhouse_container() -> Iterator[ClickHouseContainer]:
    with ClickHouseContainer(CLICKHOUSE_IMAGE) as container:
        yield container


@pytest.fixture(scope="session")
def clickhouse_endpoint(clickhouse_container: ClickHouseContainer) -> dict[str, object]:
    return {
        "host": clickhouse_container.get_container_host_ip(),
        "port": int(clickhouse_container.get_exposed_port(9000)),
        "user": clickhouse_container.username,
        "password": clickhouse_container.password,
    }


@pytest.fixture()
def clickhouse_client(clickhouse_endpoint: dict[str, object]) -> Iterator[Client]:
    db_name = f"test_{uuid.uuid4().hex[:12]}"
    admin = Client(database="default", **clickhouse_endpoint)
    admin.execute(f"CREATE DATABASE {db_name}")
    client = Client(database=db_name, **clickhouse_endpoint)
    try:
        yield client
    finally:
        client.disconnect()
        admin.execute(f"DROP DATABASE IF EXISTS {db_name}")
        admin.disconnect()
