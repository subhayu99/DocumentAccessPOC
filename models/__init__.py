from sqlmodel import SQLModel

from config import getEngine
from models.base import SQLModel, SQLModelWithID
from models.document import Document, DocumentBase
from models.user import User, UserProjectLink, UserTeamLink, RoleEnum, Project, Team, UserBase

SQLModel.metadata.create_all(getEngine())
