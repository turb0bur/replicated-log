from pydantic import BaseModel

class LogEntryCreate(BaseModel):
    message: str
    write_concern: int

class LogEntry(BaseModel):
    id: str
    message: str
    write_concern: int
    sequence_number: int