from typing import Optional
from pydantic import BaseModel, Field


class FileRequest(BaseModel):
    # Only pass .fin files
    filename: str = Field(examples=["test.fin"])
