from sqlalchemy import Column, DateTime, func, inspect
from app.shared.database.session import Base


class BaseModel(Base):
    __abstract__ = True

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def id(self):
        """Return the primary key value for this model instance.

        This property allows Pydantic's from_attributes=True to work with models
        that have explicit primary key column names (e.g., tender_id, user_id, etc.)
        instead of a generic 'id' column.
        """
        mapper = inspect(self.__class__)
        pk_columns = mapper.primary_key
        if pk_columns:
            pk_column = pk_columns[0]
            return getattr(self, pk_column.name)
        return None