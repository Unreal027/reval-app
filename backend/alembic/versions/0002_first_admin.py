"""create first admin from env

Revision ID: 0002_first_admin
Revises: 0001_init
Create Date: 2026-11-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.config import get_settings
from app.core.security import hash_password

revision: str = "0002_first_admin"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    settings = get_settings()
    if not settings.first_admin_phone or not settings.first_admin_password:
        return
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT 1 FROM users WHERE phone = :p"), {"p": settings.first_admin_phone}
    ).first()
    if exists:
        return
    conn.execute(
        sa.text(
            "INSERT INTO users (phone, name, password_hash, role, is_active) "
            "VALUES (:p, :n, :h, 'admin', true)"
        ),
        {
            "p": settings.first_admin_phone,
            "n": "管理员",
            "h": hash_password(settings.first_admin_password),
        },
    )


def downgrade() -> None:
    pass
