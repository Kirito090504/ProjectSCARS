import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from centralserver.internals.adapters.object_store import (
    BucketNames,
    get_object_store_handler,
)
from centralserver.internals.auth_handler import crypt_ctx
from centralserver.internals.config_handler import app_config
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models import (
    BucketObject,
    NewUserRequest,
    User,
    UserPublic,
    UserUpdate,
)

logger = LoggerFactory().get_logger(__name__)


def validate_username(username: str) -> bool:
    """Check if the username is valid.

    Args:
        username: The username to validate.

    Returns:
        True if the username is valid, False otherwise.
    """

    return (
        all(c.isalnum() or c in ("_", "-") for c in username)
        and len(username) > 3
        and len(username) < 22
    )


def validate_password(password: str) -> bool:
    """Make sure that the password is a valid password.

    Args:
        password: The password to validate.

    Returns:
        True if the password is valid, False otherwise.
    """

    # Password requirements:
    # - Minimum length of 8 characters
    # - At least one digit
    # - At least one lowercase letter
    # - At least one uppercase letter
    return (
        len(password) >= 8
        and any(c.isdigit() for c in password)
        and any(c.islower() for c in password)
        and any(c.isupper() for c in password)
    )


def create_user(
    new_user: NewUserRequest,
    session: Session,
) -> User:
    """Create a new user in the database.

    Args:
        new_user: The new user's information.
        session: The database session to use.

    Returns:
        A new user object.

    Raises:
        HTTPException: Thrown when the user already exists or the username is invalid.
    """

    if session.exec(select(User).where(User.username == new_user.username)).first():
        logger.warning(
            "Failed to create user: %s (username already exists)", new_user.username
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    if not validate_username(new_user.username):
        logger.warning(
            "Failed to create user: %s (invalid username)", new_user.username
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username",
        )

    if not validate_password(new_user.password):
        logger.warning(
            "Failed to create user: %s (invalid password format)", new_user.username
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password format",
        )

    # user = User(**new_user.model_dump())
    user = User(
        username=new_user.username,
        password=crypt_ctx.hash(new_user.password),
        roleId=new_user.roleId,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info("User `%s` created.", new_user.username)
    return user


def update_user_avatar(
    target_user: str, img: bytes | None, session: Session
) -> UserPublic:
    """Update the user's avatar in the database.

    Args:
        target_user: The user to update.
        img: The new avatar image.
        session: The database session to use.

    Returns:
        The updated user object.
    """

    selected_user = session.get(User, target_user)

    if not selected_user:  # Check if user exists
        logger.warning("Failed to update user: %s (user not found)", target_user)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    object_store_manager = get_object_store_handler(app_config.object_store)
    if img is None:
        if selected_user.avatarUrn is None:
            raise ValueError("No avatar to delete.")

        object_store_manager.delete(BucketNames.AVATARS, selected_user.avatarUrn)
        selected_user.avatarUrn = None

    else:
        object = object_store_manager.put(BucketNames.AVATARS, selected_user.id, img)
        selected_user.avatarUrn = object.fn

    selected_user.lastModified = datetime.datetime.now(datetime.timezone.utc)

    session.commit()
    session.refresh(selected_user)
    logger.info("User info for `%s` updated.", selected_user.username)
    return UserPublic.model_validate(selected_user)


def update_user_info(target_user: UserUpdate, session: Session) -> UserPublic:
    """Update the user's information in the database.

    Args:
        target_user: The user to update with new info.
        session: The database session to use.
    """

    selected_user = session.get(User, target_user.id)

    if not selected_user:  # Check if user exists
        logger.warning("Failed to update user: %s (user not found)", target_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    if target_user.username:  # Update username if provided
        # Check username availability
        if target_user.username != selected_user.username:
            try:
                _ = session.exec(
                    select(User).where(User.username == target_user.username)
                ).one()
                logger.warning(
                    "Failed to update user: %s (username already exists)",
                    target_user.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists",
                )

            except NoResultFound:
                logger.debug("Username %s is available.", target_user.username)

        # Check username validity
        if not validate_username(target_user.username):
            logger.warning(
                "Failed to update user: %s (invalid username)", target_user.username
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username",
            )

        # Set new username
        selected_user.username = target_user.username

    if target_user.email:  # Update email if provided
        selected_user.email = target_user.email

    if target_user.nameFirst:  # Update first name if provided
        selected_user.nameFirst = target_user.nameFirst

    if target_user.nameMiddle:  # Update middle name if provided
        selected_user.nameMiddle = target_user.nameMiddle

    if target_user.nameLast:  # Update last name if provided
        selected_user.nameLast = target_user.nameLast

    if target_user.password:  # Update password if provided
        if not validate_password(target_user.password):  # Validate password
            logger.warning(
                "Failed to update user: %s (invalid password format)",
                target_user.username,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password format",
            )

        # Set new password
        selected_user.password = crypt_ctx.hash(target_user.password)

    selected_user.lastModified = datetime.datetime.now(datetime.timezone.utc)

    session.commit()
    session.refresh(selected_user)
    logger.info("User info for `%s` updated.", selected_user.username)
    return UserPublic.model_validate(selected_user)


def get_user_avatar(fn: str) -> BucketObject:
    return get_object_store_handler(app_config.object_store).get(
        BucketNames.AVATARS, fn
    )
