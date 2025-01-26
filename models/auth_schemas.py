import datetime
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    email: str
    class Config:
        from_attributes: True

class UserCreate(UserBase):
    pass

class User(UserBase):
    pass

class AddressBase(BaseModel):
    pass

class GenerateUserToken(BaseModel):
    pass

class GenerateOtp(BaseModel):
    email: str

class VerifyOtp(BaseModel):
    email: str
    otp: int