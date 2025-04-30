import os

from centralserver.internals.adapters.config import (
    LocalObjectStoreAdapterConfig,
    MinIOObjectStoreAdapterConfig,
)


def test_valid_local_config():
    """Test the Local object store configuration."""

    config = LocalObjectStoreAdapterConfig("pytest-path")

    assert config.info["filepath"] == "pytest-path"


def test_empty_local_config():
    """Test the Local object store configuration with empty filepath."""

    config = LocalObjectStoreAdapterConfig()

    # Default is used if empty string
    assert config.info["filepath"] == os.path.join(os.getcwd(), "data")


def test_valid_minio_config():
    """Test the MinIO object store configuration."""

    config = MinIOObjectStoreAdapterConfig(
        access_key="bf51e071508becb67bf2263c9f60403f",
        secret_key="533af9863ea0252a5607bb397dbc3fc1",
    )

    assert config.info["access_key_set"] is True
    assert config.info["secret_key_set"] is True
    assert config.info["endpoint"] == "localhost:9000"
    assert config.info["secure"] is False


def test_no_access_key_minio_config():
    """Test the MinIO object store configuration with no access key."""

    sk = "533af9863ea0252a5607bb397dbc3fc1"
    try:
        _ = MinIOObjectStoreAdapterConfig(
            secret_key=sk,
        )

    except ValueError:
        pass

    else:
        raise AssertionError("ValueError not raised")


def test_no_secret_key_minio_config():
    """Test the MinIO object store configuration with no secret key."""

    ak = "bf51e071508becb67bf2263c9f60403f"
    try:
        _ = MinIOObjectStoreAdapterConfig(
            access_key=ak,
        )

    except ValueError:
        pass

    else:
        raise AssertionError("ValueError not raised")
