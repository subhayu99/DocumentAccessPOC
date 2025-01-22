from typing import Any

from sqlmodel import Field, SQLModel as BaseSQLModel, Session, select

from config import getEngine


class SQLModel(BaseSQLModel):

    @classmethod
    def get(cls, key: Any | tuple | dict):
        with Session(getEngine()) as db:
            return db.get(cls, key)

    def create(self):
        with Session(getEngine()) as db:
            db.add(self)
            db.commit()
            db.refresh(self)
            return self

    def update(self):
        with Session(getEngine()) as db:
            db.add(self)
            db.commit()
            db.refresh(self)
            return self
    
    def upsert(self):
        try:
            return self.update()
        except:
            try:
                return self.create()
            except:
                print(f"Failed to upsert {self.__class__.__name__} with {self}")

    def delete(self):
        with Session(getEngine()) as db:
            db.delete(self)
            db.commit()

    @classmethod
    def delete_by_fields(cls, **fields):
        with Session(getEngine()) as db:
            obj = db.exec(select(cls).where(**fields)).first()
            if obj:
                db.delete(obj)
                db.commit()

    @classmethod
    def get_by_fields(cls, *whereclause):
        with Session(getEngine()) as db:
            return db.exec(select(cls).where(*whereclause)).all()

    @classmethod
    def get_all(cls):
        with Session(getEngine()) as db:
            return db.exec(select(cls)).all()

    @staticmethod
    def create_all(instances: list["SQLModel"]):
        with Session(getEngine()) as db:
            db.add_all(instances)
            db.commit()

    @classmethod
    def select(cls):
        return select(cls)

    @staticmethod
    def exec(*args, **kwargs):
        with Session(getEngine()) as db:
            return db.exec(*args, **kwargs)

class SQLModelWithID(SQLModel):
    id: str = Field(primary_key=True)

    @classmethod
    def get_by_id(cls, _id: str):
        with Session(getEngine()) as db:
            return db.get(cls, _id)
    
    @classmethod
    def get_by_ids(cls, _ids: list[str]):
        with Session(getEngine()) as db:
            return db.exec(select(cls).where(cls.id.in_(_ids))).all()

    @classmethod
    def delete_by_id(cls, _id: str):
        with Session(getEngine()) as db:
            obj = db.exec(select(cls).where(cls.id == _id)).first()
            if obj:
                db.delete(obj)
                db.commit()
