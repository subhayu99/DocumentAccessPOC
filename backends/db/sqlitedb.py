import sqlite3

from backends.db.abstractdb import AbstractDatabase


class SQLiteDatabase(AbstractDatabase):
    """SQLite implementation of the DatabaseInterface."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def execute_query(self, query: str, params: tuple = ()):
        if not self.connection:
            raise ConnectionError("Database not connected.")
        self.cursor.execute(query, params)

    def fetch_one(self):
        return self.cursor.fetchone()

    def fetch_all(self):
        return self.cursor.fetchall()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
