from pydantic import BaseModel, ConfigDict, field_validator, validator
from pydantic.types import UUID4
from src.utils.enums import lobbystage, winners

class Token(BaseModel):
    token: str
    token_type: str
