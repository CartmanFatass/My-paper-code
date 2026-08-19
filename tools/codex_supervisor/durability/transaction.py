"""BEGIN IMMEDIATE owner for durability-kernel writes."""

from __future__ import annotations

import sqlite3


class DurabilityTransaction:
    """One explicit immediate transaction. Do not nest `with connection:`."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def __enter__(self) -> DurabilityTransaction:
        if self.connection.in_transaction:
            raise RuntimeError("durability transaction already open")
        self.connection.execute("BEGIN IMMEDIATE")
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object) -> None:
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
