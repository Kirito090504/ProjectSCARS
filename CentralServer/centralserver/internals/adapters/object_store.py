import hashlib
import os
from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO
from typing import Final, override

from minio import Minio

from centralserver.internals.adapters.config import (
    LocalObjectStoreAdapterConfig,
    MinIOObjectStoreAdapterConfig,
    ObjectStoreAdapterConfig,
)
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models import BucketObject

logger = LoggerFactory().get_logger(__name__)


class BucketNames(Enum):
    AVATARS = "centralserver-avatars"
    REPORT_EXPORTS = "centralserver-reports"


class ObjectStoreAdapter(ABC):
    """Superclass for object store adapter configuration."""

    @abstractmethod
    def check(self) -> None:
        """Verify the health of the object store."""

    @abstractmethod
    def put(self, bucket: BucketNames, fn: str, obj: bytes) -> BucketObject:
        """Put the object into the object store and return its ID.

        Args:
            bucket: The name of the bucket to put the object into.
            fn: The name of the file in the object store.
            obj: The object to put into the object store.
        """

    @abstractmethod
    def get(self, bucket: BucketNames, hashed_filename: str) -> BucketObject:
        """Get the object with the given ID from the object store."""

    @abstractmethod
    def delete(self, bucket: BucketNames, hashed_filename: str) -> None:
        """Delete the object with the given ID from the object store."""


class LocalObjectStoreAdapter(ObjectStoreAdapter):
    """Use the local filesystem as the central server's object store."""

    _ENCODING: Final[str] = "utf-8"

    def __init__(self, config: LocalObjectStoreAdapterConfig) -> None:
        """Initialize the local object store adapter.

        Args:
            config: The configuration for the local object store.
        """

        self.config = config

    @staticmethod
    def validate_object_name(object_name: str) -> bool:
        """Check if the object name is valid."""

        allowed_symbols = {"-", ".", "_"}
        # NOTE: Object name requirements:
        # - Must be between 3 and 255 characters long.
        # - Must be alphanumeric or one of the following characters: - . _
        # - Must not start or end with symbols.
        return (
            3 <= len(object_name) <= 255
            and all(c.isalnum() or c in allowed_symbols for c in object_name)
            and not (
                object_name[0] in allowed_symbols or object_name[-1] in allowed_symbols
            )
        )

    def get_object_filesystem_filename(self, fn: str) -> str:
        return hashlib.sha256(fn.encode(self._ENCODING)).hexdigest()

    @override
    def check(self) -> None:
        logger.debug("Ensuring existence of local object store directories.")
        self.config.filepath.mkdir(parents=True, exist_ok=True)
        for directory in BucketNames:
            logger.debug(f"Ensuring existence of directory: {directory.value}")
            subdir = self.config.filepath / directory.value
            subdir.mkdir(parents=True, exist_ok=True)

    @override
    def put(self, bucket: BucketNames, fn: str, obj: bytes) -> BucketObject:
        logger.debug("Putting object into local object store.")
        if not self.validate_object_name(fn):
            raise ValueError(f"Invalid object name: {fn}")

        hashed_filename = self.get_object_filesystem_filename(fn)
        new_file_dir = self.config.filepath / bucket.value / hashed_filename[:2]
        new_file_dir.mkdir(parents=True, exist_ok=True)
        new_fp = new_file_dir / hashed_filename
        if new_fp.exists():
            raise FileExistsError("File already exists. Please use a different name.")

        with open(
            self.config.filepath / bucket.value / hashed_filename[:2] / hashed_filename,
            "wb",
        ) as f:
            f.write(obj)

        return BucketObject(
            bucket=bucket.value,
            fn=hashed_filename,
            obj=obj,
        )

    @override
    def get(self, bucket: BucketNames, hashed_filename: str) -> BucketObject:
        logger.debug("Getting object from local object store.")
        object_fp = (
            self.config.filepath / bucket.value / hashed_filename[:2] / hashed_filename
        )
        if not object_fp.exists():
            raise FileNotFoundError(f"File {object_fp} does not exist.")

        data = object_fp.read_bytes()

        return BucketObject(
            bucket=bucket.value,
            fn=hashed_filename,
            obj=data,
        )

    @override
    def delete(self, bucket: BucketNames, hashed_filename: str) -> None:
        logger.debug("Deleting object from local object store.")
        object_fp = (
            self.config.filepath / bucket.value / hashed_filename[:2] / hashed_filename
        )
        if not object_fp.exists():
            raise FileNotFoundError(f"File {object_fp} does not exist.")

        os.remove(object_fp)


class MinIOObjectStoreAdapter(ObjectStoreAdapter):
    """Use MinIO as the central server's object store."""

    def __init__(self, config: MinIOObjectStoreAdapterConfig):
        """Initialize the MinIO object store adapter.

        Args:
            config: The configuration for the MinIO object store.
        """

        self.config = config

        self.client = Minio(
            config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )

    @staticmethod
    def validate_object_name(object_name: str) -> bool:
        """Check if the object name is valid."""

        allowed_symbols = {"-", ".", "_"}
        # NOTE: Object name requirements:
        # - Must be between 3 and 255 characters long.
        # - Must be alphanumeric or one of the following characters: - . _
        # - Must not start or end with symbols.
        return (
            3 <= len(object_name) <= 255
            and all(c.isalnum() or c in allowed_symbols for c in object_name)
            and not (
                object_name[0] in allowed_symbols or object_name[-1] in allowed_symbols
            )
        )

    @override
    def check(self) -> None:
        logger.debug("Ensuring existence of MinIO buckets.")
        for bucket in BucketNames:
            logger.debug(f"Ensuring existence of bucket: {bucket.value}")
            if not self.client.bucket_exists(bucket.value):
                logger.debug(f"Creating bucket: {bucket.value}")
                self.client.make_bucket(bucket.value)

    @override
    def put(self, bucket: BucketNames, fn: str, obj: bytes) -> BucketObject:
        logger.debug("Putting object into MinIO object store.")
        if not self.validate_object_name(fn):
            raise ValueError(f"Invalid object name: {fn}")

        length = len(obj)
        self.client.put_object(
            bucket_name=bucket.value,
            object_name=fn,
            data=BytesIO(obj),
            length=length,
        )

        return BucketObject(
            bucket=bucket.value,
            fn=fn,
            obj=obj,
        )

    @override
    def get(self, bucket: BucketNames, hashed_filename: str) -> BucketObject:
        logger.debug("Getting object from MinIO object store.")
        response = None
        try:
            response = self.client.get_object(
                bucket_name=bucket.value, object_name=hashed_filename
            )
            response_data = response.read()

        finally:
            if response is not None:
                logger.debug("Closing MinIO response.")
                # Close the response to release the connection
                # and avoid resource leaks.
                response.close()  # WARN: Why are these not implemented according to source?
                response.release_conn()

        return BucketObject(
            bucket=bucket.value,
            fn=hashed_filename,
            obj=response_data,
        )

    @override
    def delete(self, bucket: BucketNames, hashed_filename: str) -> None:
        logger.debug("Deleting object from MinIO object store.")
        try:
            self.client.remove_object(bucket.value, hashed_filename)
        except Exception as e:
            raise FileNotFoundError(f"File {hashed_filename} does not exist.") from e


def get_object_store_handler(conf: ObjectStoreAdapterConfig) -> ObjectStoreAdapter:
    """Get the appropriate object store adapter based on the configuration.

    Args:
        The object store adapter configuration.

    Returns:
        The object store adapter instance.
    """

    if isinstance(conf, LocalObjectStoreAdapterConfig):
        logger.debug("Using local object store adapter.")
        return LocalObjectStoreAdapter(conf)

    elif isinstance(conf, MinIOObjectStoreAdapterConfig):
        logger.debug("Using MinIO object store adapter.")
        return MinIOObjectStoreAdapter(conf)

    else:
        logger.error("Invalid object store configuration.")
        raise ValueError("Invalid object store configuration.")
