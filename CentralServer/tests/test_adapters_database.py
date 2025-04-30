import os
from pathlib import Path

from centralserver.internals.adapters.config import (
    MySQLDatabaseConfig,
    SQLiteDatabaseConfig,
)


def test_valid_sqlite_config():
    """Test the SQLite database configuration."""

    config = SQLiteDatabaseConfig(filepath="test.db")

    assert str(config.filepath.absolute()) == str(
        Path(os.getcwd(), "test.db").absolute()
    )
    assert config.info["sqlalchemy_uri"] == f"sqlite:///{config.filepath.absolute()}"
    assert config.info["connect_args"] == {"check_same_thread": False}


def test_empty_sqlite_config():
    """Test the SQLite database configuration with empty filepath."""

    config = SQLiteDatabaseConfig(filepath="")
    # Default is used if empty string
    assert str(config.filepath.absolute()) == str(
        Path(os.getcwd(), "centralserver.db").absolute()
    )
    assert config.info["sqlalchemy_uri"] == f"sqlite:///{config.filepath.absolute()}"
    assert config.info["connect_args"] == {"check_same_thread": False}


def test_valid_mysql_config():
    """Test the MySQL database configuration."""

    config = MySQLDatabaseConfig(
        host="192.168.0.252",
        port=3306,
        username="sample_user",
        password="password123",
        database="test_db",
    )

    assert (
        config.info["sqlalchemy_uri"]
        == "mysql+pymysql://sample_user:password123@192.168.0.252:3306/test_db"
    )
