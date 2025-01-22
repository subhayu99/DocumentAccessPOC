import uuid
from datetime import datetime

from sqlmodel import Relationship, Field
from betterpassphrase import generate_phrase

from models.enums import RoleEnum
from helpers.aes import AESHelper as AES
from models.base import SQLModelWithID, SQLModel
from helpers.rsa import RSAHelper as RSA, KeyFormat


class UserProjectLink(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id", primary_key=True)
    role: RoleEnum = Field(
        default=RoleEnum.MEMBER, description="Role specific to user in this project"
    )


class UserTeamLink(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    team_id: uuid.UUID = Field(foreign_key="team.id", primary_key=True)
    role: RoleEnum = Field(
        default=RoleEnum.MEMBER, description="Role specific to user in this team"
    )


class Group(SQLModelWithID):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.now)


class Team(Group, table=True):
    members: list["User"] = Relationship(
        back_populates="teams", link_model=UserTeamLink
    )


class Project(Group, table=True):
    started_at: datetime | None = Field(default=None)
    members: list["User"] = Relationship(
        back_populates="projects", link_model=UserProjectLink
    )


class UserBase(SQLModelWithID):
    id: str = Field(primary_key=True)
    name: str
    email: str
    designation: str


class UserCreateResponse(UserBase):
    parmanent_password: str
    note: str = "Save this parmanent password for future use. This is the only time you will see it."


class User(UserBase, table=True):
    public_key: str
    encrypted_private_key: str
    created_at: datetime = Field(default_factory=datetime.now)
    # Many-to-many relationships via intermediary tables
    teams: list[Team] = Relationship(back_populates="members", link_model=UserTeamLink)
    projects: list[Project] = Relationship(
        back_populates="members", link_model=UserProjectLink
    )
    shared_keys: list["SharedKeyRegistry"] = Relationship(  # noqa: F821
        back_populates="user",
        sa_relationship_kwargs={"primaryjoin": "SharedKeyRegistry.user_id == User.id"},
        cascade_delete=True,
    )

    @classmethod
    def from_base(cls, user: UserBase):
        private_key, public_key = RSA.generate_key_pair(out_format=KeyFormat.STRING)
        parmanent_password = generate_phrase(length=8, sep="-", capitalize=False).passphrase
        encrypted_private_key = AES(parmanent_password).encrypt(private_key.encode())
        
        user_obj = cls(
            id=user.id,
            name=user.name,
            email=user.email,
            designation=user.designation,
            public_key=public_key,
            encrypted_private_key=encrypted_private_key.hex(),
        ).create()
        
        return UserCreateResponse(
            id=user_obj.id,
            name=user_obj.name,
            email=user_obj.email,
            designation=user_obj.designation,
            parmanent_password=parmanent_password,
        )

    @classmethod
    def get_id_obj_map(cls, user_ids: list[str]):
        users = cls.get_by_ids(user_ids)
        return {user.id: user for user in users}

    def get_private_key(self, password: str):
        return AES(password).decrypt(bytes.fromhex(self.encrypted_private_key)).decode()

    def verify_private_key(self, password: str):
        """Verifies that the given private key matches the public key of the user. Returns True if the key is valid, False otherwise."""
        return RSA.verify_key_pair(self.get_private_key(password), self.public_key)

    def verify_password(self, password: str):
        return self.verify_private_key(password)


class UserWithPrivateKey(SQLModel):
    user: User
    private_key: str
