# models.py
from pydantic import BaseModel, Field

class ExtractedInfo(BaseModel):
    course_name: str = Field(description="The name of the course")
    semester: str = Field(description="The semester of the test")
    year: str = Field(description="The year of the test")
    moed: str = Field(description="The moed of the test")
    degree: str = Field(description="The degree")