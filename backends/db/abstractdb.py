from abc import ABC, abstractmethod


class AbstractDatabase(ABC):
    """Abstract base class for database operations."""

    @abstractmethod
    def connect(self):
        """Establish a connection to the database."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()):
        """Execute a query against the database."""
        pass

    @abstractmethod
    def fetch_one(self):
        """Fetch one record from the executed query."""
        pass

    @abstractmethod
    def fetch_all(self):
        """Fetch all records from the executed query."""
        pass

    @abstractmethod
    def close(self):
        """Close the database connection."""
        pass

    def __enter__(self):
        """Enter the runtime context for this database connection."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and close the database connection."""
        self.close()
