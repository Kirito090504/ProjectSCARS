import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from centralserver.internals.auth_handler import (
    get_user,
    verify_access_token,
    verify_user_permission,
)
from centralserver.internals.db_handler import get_db_session
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models.reports.monthly_report import (
    MonthlyReport,
    ReportStatus,
)
from centralserver.internals.models.token import DecodedJWTToken

logger = LoggerFactory().get_logger(__name__)

router = APIRouter(
    prefix="/v1/reports",
    tags=["reports"],
    dependencies=[Depends(verify_access_token)],
)

logged_in_dep = Annotated[DecodedJWTToken, Depends(verify_access_token)]


@router.get("/monthly")
async def get_all_monthly_reports(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    offset: int = 0,
    limit: int = 10,
) -> list[MonthlyReport]:
    """Get all monthly reports with pagination."""

    if not await verify_user_permission("reports:global:read", session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view monthly reports.",
        )

    logger.debug(
        "user `%s` requesting monthly reports of all schools with offset %s and limit %s.",
        token.id,
        offset,
        limit,
    )

    return list(session.exec(select(MonthlyReport).offset(offset).limit(limit)).all())


@router.get("/monthly/{school_id}")
async def get_school_monthly_reports(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    offset: int = 0,
    limit: int = 10,
) -> list[MonthlyReport]:
    """Get monthly reports of a specific school with pagination."""

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:read" if user.schoolId == school_id else "reports:global:read"
    )

    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view monthly reports.",
        )

    logger.debug(
        "user `%s` requesting monthly reports of school %s with offset %s and limit %s.",
        token.id,
        school_id,
        offset,
        limit,
    )

    return list(
        session.exec(
            select(MonthlyReport)
            .where(MonthlyReport.submittedBySchool == school_id)
            .offset(offset)
            .limit(limit)
        ).all()
    )


@router.get("/monthly/{school_id}/{year}/{month}")
async def get_school_monthly_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    offset: int = 0,
    limit: int = 10,
) -> MonthlyReport:
    """Get monthly reports of a school with pagination."""

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:read" if user.schoolId == school_id else "reports:global:read"
    )

    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view monthly reports.",
        )

    logger.debug(
        "user `%s` requesting monthly reports of school %s with offset %s and limit %s.",
        token.id,
        school_id,
        offset,
        limit,
    )

    report = session.exec(
        select(MonthlyReport).where(
            MonthlyReport.id == datetime.date(year=year, month=month, day=1)
        )
    ).one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly report not found.",
        )

    return report


@router.put("/monthly/{school_id}/{year}/{month}")
async def create_school_monthly_report(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
    school_id: int,
    year: int,
    month: int,
    name: str | None = None,
) -> MonthlyReport:
    """Create a monthly report of a school."""

    user = await get_user(token.id, session, by_id=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    required_permission = (
        "reports:local:write" if user.schoolId == school_id else "reports:global:write"
    )

    if not await verify_user_permission(required_permission, session, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create monthly reports.",
        )

    logger.debug(
        "user `%s` creating monthly report of school %s for %s-%s.",
        token.id,
        school_id,
        year,
        month,
    )

    report = session.exec(
        select(MonthlyReport).where(
            MonthlyReport.id == datetime.date(year=year, month=month, day=1)
        )
    ).one_or_none()

    if report is not None:
        logger.debug(
            "Monthly report for %s-%s already exists.",
            year,
            month,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Monthly report for this month already exists.",
        )

    report = MonthlyReport(
        id=datetime.date(year=year, month=month, day=1),
        name=name,
        submittedBySchool=school_id,
        reportStatus=ReportStatus.DRAFT,
        preparedBy=user.id,
        lastModified=datetime.datetime.now(),
    )

    session.add(report)
    session.commit()
    session.refresh(report)

    return report
