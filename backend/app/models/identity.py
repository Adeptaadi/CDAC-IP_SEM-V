import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, SmallInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    user_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    roles = relationship("Role", secondary="user_roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(GUID, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(SmallInteger, ForeignKey("roles.role_id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
