from pydantic import BaseModel, EmailStr, Field, ConfigDict


class StudentCreate(BaseModel):
    student_name: str
    email: EmailStr
    password: str = Field(min_length=8)


class StudentLogin(BaseModel):
    email: EmailStr
    password: str


class StudentResponse(BaseModel):
    student_id: int
    student_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)