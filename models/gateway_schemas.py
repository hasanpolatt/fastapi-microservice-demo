from pydantic import BaseModel

# Pydantic models for request body validation.
class GenerateUserToken(BaseModel):
    username: str
    password: str


class UserCredentials(BaseModel):
    username: str
    password: str


class UserRegistration(BaseModel):
    username: str
    email: str
    password: str


class GenerateOtp(BaseModel):
    email: str


class VerifyOtp(BaseModel):
    email: str
    otp: int