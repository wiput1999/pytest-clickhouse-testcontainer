# pytest-testcontainer

Pytest + [testcontainers](https://testcontainers-python.readthedocs.io/) running ClickHouse in Docker for integration tests.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker running locally

## Layout

```
.
├── pyproject.toml              # uv project + pytest config
├── uv.lock                     # locked deps
└── tests/
    ├── conftest.py             # session-scoped ClickHouse container, per-test isolated DB
    └── test_clickhouse.py      # sample tests
```

## Fixtures (`tests/conftest.py`)

- `clickhouse_container` — session-scoped, boots `clickhouse/clickhouse-server:25.10-alpine` once.
- `clickhouse_endpoint` — host/port/user/password dict.
- `clickhouse_client` — function-scoped `clickhouse_driver.Client` with a fresh `test_<uuid>` database; dropped on teardown.

## Run

```bash
uv sync                # install deps
uv run pytest          # run all tests
uv run pytest -v       # verbose
uv run pytest -k name  # filter by test name
```

First run pulls the ClickHouse image (~150 MB) and takes ~25 s. Subsequent runs reuse the image.

## Add a test

```python
def test_something(clickhouse_client):
    clickhouse_client.execute("CREATE TABLE t (id UInt64) ENGINE = Memory")
    clickhouse_client.execute("INSERT INTO t VALUES", [(1,)])
    assert clickhouse_client.execute("SELECT id FROM t") == [(1,)]
```

Each test gets its own database — no cleanup needed.

## Add deps

```bash
uv add <pkg>           # runtime
uv add --dev <pkg>     # dev/test only
```
