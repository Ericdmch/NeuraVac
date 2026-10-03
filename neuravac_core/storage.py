"""Local mission audit trail; parameterized writes and explicit export allowlist."""

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from neuravac_core.utils.logging import redact

TABLES = ("missions", "cleaning_regions", "cleaning_attempts", "safety_events", "ai_decisions")


class MissionStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        for table in TABLES:
            self.connection.execute(
                f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY, mission_id TEXT NOT NULL, timestamp REAL NOT NULL, payload TEXT NOT NULL)"
            )
        self.connection.commit()

    def record(
        self, table: str, mission_id: str, timestamp: float, payload: dict[str, Any]
    ) -> None:
        if table not in TABLES:
            raise ValueError("unknown audit table")
        self.connection.execute(
            f"INSERT INTO {table} (mission_id,timestamp,payload) VALUES (?,?,?)",
            (mission_id, timestamp, json.dumps(redact(payload), allow_nan=False)),
        )
        self.connection.commit()

    def export_table(self, table: str, mission_id: str | None = None) -> list[dict[str, Any]]:
        if table not in TABLES:
            raise ValueError("unknown audit table")
        query = f"SELECT id,mission_id,timestamp,payload FROM {table}"
        params: tuple[str, ...] = ()
        if mission_id is not None:
            query += " WHERE mission_id=?"
            params = (mission_id,)
        return [
            dict(id=i, mission_id=m, timestamp=t, **json.loads(payload))
            for i, m, t, payload in self.connection.execute(query, params)
        ]

    def export_csv(self, table: str, path: str | Path) -> None:
        rows = self.export_table(table)
        with Path(path).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=sorted({key for row in rows for key in row}))
            writer.writeheader()
            writer.writerows(rows)

    def close(self) -> None:
        self.connection.close()
