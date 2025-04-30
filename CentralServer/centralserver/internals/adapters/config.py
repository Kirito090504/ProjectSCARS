import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, override

##### Database Adapter Configurations #####


class DatabaseAdapterConfig(ABC):
    """Superclass for database adapter configuration."""

    @property
    @abstractmethod
    def info(self) -> dict[str, Any]:
        """Get the database adapter information."""

    @property
    @abstractmethod
    def sqlalchemy_uri(self) -> str:
        """Get the database URI for SQLAlchemy."""

    @property
    @abstractmethod
    def connect_args(self) -> dict[str, Any]:
        """Get the connection arguments for SQLAlchemy."""


class SQLiteDatabaseConfig(DatabaseAdapterConfig):
    """The SQLite database configuration."""

    def __init__(
        self,
        filepath: str | Path | None = None,
        connect_args: dict[str, Any] | None = None,
    ):
        """Configuration for a SQLite database engine.

        Args:
            filepath: The location of the SQLite database file.
            connect_args: The connection arguments to use.
        """

        default_connect_args: dict[str, Any] = {"check_same_thread": False}

        self.filepath: Path = Path(
            filepath or os.path.join(os.getcwd(), "centralserver.db")
        )

        self._connect_args = {**default_connect_args, **(connect_args or {})}

    @property
    @override
    def info(self) -> dict[str, Any]:
        return {
            "name": "SQLite",
            "filepath": str(self.filepath),
            "connect_args": self._connect_args,
            "sqlalchemy_uri": self.sqlalchemy_uri,
        }

    @property
    @override
    def sqlalchemy_uri(self) -> str:
        """Get the database URI for SQLAlchemy."""

        return f"sqlite:///{self.filepath.absolute()}"

    @property
    @override
    def connect_args(self) -> dict[str, Any]:
        return self._connect_args


class MySQLDatabaseConfig(DatabaseAdapterConfig):
    """The MySQL database configuration."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        connect_args: dict[str, Any] | None = None,
    ):
        """Create a configuration object for the database.

        Args:
            username: The database username.
            password: The database password.
            host: The hostname of the database server.
            port: The port number of the database server.
            database: The database name.
            connect_args: The connection arguments to use.
        """

        default_connect_args: dict[str, Any] = {}

        self.username: str = username or "ProjectSCARS_DatabaseAdmin"
        self.password: str = password or "ProjectSCARS_mysql143"
        self.host: str = host or "localhost"
        self.port: int = port or 3306
        self.database: str = database or "ProjectSCARS_CentralServer"
        self._connect_args = {**default_connect_args, **(connect_args or {})}

    @property
    @override
    def info(self) -> dict[str, Any]:
        """Get the name of the database adapter."""
        return {
            "name": "MySQL",
            "username": self.username,
            "password_set": self.password != "",
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "connect_args": self._connect_args,
            "sqlalchemy_uri": self.sqlalchemy_uri,
        }

    @property
    @override
    def sqlalchemy_uri(self) -> str:
        """Get the database URI for SQLAlchemy."""
        return "mysql+pymysql://{username}:{password}@{host}:{port}/{database}".format(
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    @property
    @override
    def connect_args(self) -> dict[str, Any]:
        return self._connect_args


##### Object Store Adapter Configurations #####


class ObjectStoreAdapterConfig(ABC):
    """Adapter configuration for object store."""

    @property
    @abstractmethod
    def info(self) -> dict[str, Any]:
        """Get the object store adapter information"""


class LocalObjectStoreAdapterConfig(ObjectStoreAdapterConfig):
    """Adapter configuration for local object store."""

    def __init__(self, filepath: str | None = None) -> None:
        self.filepath: Path = Path(filepath or os.path.join(os.getcwd(), "data"))

    @property
    @override
    def info(self) -> dict[str, Any]:
        """Get the object store adapter information."""

        return {
            "name": "Local",
            "filepath": str(self.filepath),
        }


class MinIOObjectStoreAdapterConfig(ObjectStoreAdapterConfig):
    """Adapter configuration for MinIO."""

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint: str | None = None,
        secure: bool | None = None,
    ):
        """Configuration for MinIO object store adapter.

        Args:
            access_key: The access key for MinIO. (required)
            secret_key: The secret key for MinIO. (required)
            endpoint: The URL of the MinIO server. (default: localhost:9000)
            secure: Use secure (TLS) connection. (default: False).
        """

        if access_key is None or secret_key is None:
            raise ValueError("The access key and secret key are required.")

        self.access_key: str = access_key
        self.secret_key: str = secret_key
        self.endpoint: str = endpoint or "localhost:9000"
        self.secure: bool = secure or False

    @property
    @override
    def info(self) -> dict[str, Any]:
        return {
            "name": "MinIO",
            "access_key_set": self.access_key != "",
            "secret_key_set": self.secret_key != "",
            "endpoint": self.endpoint,
            "secure": self.secure,
        }
