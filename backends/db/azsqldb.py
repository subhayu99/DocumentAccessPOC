import pyodbc

from backends.db.abstractdb import AbstractDatabase


class AzureSQLDatabase(AbstractDatabase):
    """Azure SQL Database implementation of the DatabaseInterface."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = pyodbc.connect(self.connection_string)
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
