from pydantic import BaseModel

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
