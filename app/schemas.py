"""Shared API request contracts: coordinate changes with the integration owner."""
from pydantic import BaseModel, Field

class Settings(BaseModel):
 city:str='Singapore'
 variable:str='T2M'
 start:int=2001
 end:int=2025


class Question(BaseModel):
 question:str=Field(max_length=2000)


class Writing(BaseModel):
 result_id:str|None=None
 settings:Settings=Field(default_factory=Settings)
 question:str=Field(default='',max_length=2000)
 hypothesis:str=Field(default='',max_length=200)
 observation:str=Field(default='',max_length=4000)
 conclusion:str=Field(default='',max_length=12000)
 reviewed:bool=False
 message:str=Field(default='',max_length=2000)

