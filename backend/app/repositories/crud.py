from sqlalchemy import select
from sqlalchemy.orm import Session


class Repository:
    """Queries and persistence only. The service owns validation and transactions."""
    def __init__(self, db: Session, model):
        self.db, self.model = db, model

    def get(self, record_id, *, lock=False):
        statement = select(self.model).where(self.model.id == record_id)
        if lock:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def list(self, offset, limit, filters):
        statement = select(self.model)
        if hasattr(self.model, "deleted_at"):
            statement = statement.where(self.model.deleted_at.is_(None))
        for key, value in filters.items():
            statement = statement.where(getattr(self.model, key) == value)
        return self.db.scalars(statement.order_by(self.model.id).offset(offset).limit(limit)).all()

    def add(self, values):
        record = self.model(**values)
        self.db.add(record)
        return record

    def delete(self, record):
        self.db.delete(record)
