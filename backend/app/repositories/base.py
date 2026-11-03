from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session
from contextlib import contextmanager

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository providing common transactional CRUD operations."""

    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, entity_id: Any) -> Optional[T]:
        return self.db.query(self.model).filter(
            getattr(self.model, self._primary_key_name()) == entity_id
        ).first()

    def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        return self.db.query(self.model).offset(offset).limit(limit).all()

    def create(self, entity: T) -> T:
        self.db.add(entity)
        self.db.flush()
        return entity

    def update(self, entity: T) -> T:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.db.delete(entity)
        self.db.flush()

    def _primary_key_name(self) -> str:
        mapper = getattr(self.model, "__mapper__", None)
        if mapper and mapper.primary_key:
            return mapper.primary_key[0].name
        return "id"
