import uuid
from sqlalchemy import Column, String, JSON, TypeDecorator

try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB, ARRAY as PG_ARRAY
except ImportError:
    PG_UUID, PG_JSONB, PG_ARRAY = None, None, None


class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses PostgreSQL's UUID, otherwise String(36)."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PG_UUID is not None:
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value) if isinstance(value, uuid.UUID) else str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            return value


class ArrayUUIDType(TypeDecorator):
    """Platform-independent UUID array. Serializes to PostgreSQL ARRAY or JSON list of string UUIDs."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PG_ARRAY is not None and PG_UUID is not None:
            return dialect.type_descriptor(PG_ARRAY(PG_UUID(as_uuid=True)))
        return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(v) if isinstance(v, uuid.UUID) else str(v) for v in value]
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return value


JSONB_TYPE = JSON().with_variant(PG_JSONB, "postgresql") if PG_JSONB is not None else JSON
ARRAY_STRING = JSON().with_variant(PG_ARRAY(String), "postgresql") if PG_ARRAY is not None else JSON
ARRAY_UUID = ArrayUUIDType
