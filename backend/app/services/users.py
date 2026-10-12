from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.models import User, UserRole


def ensure_bootstrap_users(session: Session) -> None:
    settings = get_settings()
    entries = [
        ("admin", "系统管理员", UserRole.ADMIN, settings.bootstrap_admin_password),
        ("researcher", "研究员", UserRole.RESEARCHER, settings.bootstrap_researcher_password),
        ("viewer", "只读用户", UserRole.VIEWER, settings.bootstrap_viewer_password),
    ]
    changed = False
    for username, display_name, role, password in entries:
        if session.scalar(select(User).where(User.username == username)) is None:
            session.add(User(username=username, display_name=display_name, role=role, password_hash=hash_password(password)))
            changed = True
    if changed:
        session.commit()


def list_users(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.created_at)))


def create_user(session: Session, *, username: str, display_name: str, password: str, role: UserRole) -> User:
    if session.scalar(select(User).where(User.username == username)) is not None:
        raise ValueError("用户名已存在")
    user = User(username=username, display_name=display_name, password_hash=hash_password(password), role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(
    session: Session,
    user: User,
    *,
    actor_id: str,
    display_name: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> User:
    if user.id == actor_id and is_active is False:
        raise ValueError("管理员不能停用自己的账号")
    if user.id == actor_id and role is not None and role != UserRole.ADMIN:
        raise ValueError("管理员不能降低自己的角色")
    removes_admin = user.role == UserRole.ADMIN and user.is_active and (
        is_active is False or (role is not None and role != UserRole.ADMIN)
    )
    if removes_admin:
        other_admin = session.scalar(
            select(User).where(User.role == UserRole.ADMIN, User.is_active.is_(True), User.id != user.id)
        )
        if other_admin is None:
            raise ValueError("系统必须保留至少一个可用管理员")
    if display_name is not None:
        user.display_name = display_name
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    session.commit()
    session.refresh(user)
    return user
