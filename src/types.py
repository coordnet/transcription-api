from dataclasses import dataclass, field
from datetime import datetime


# Type for transcriptions in the database
@dataclass
class Transcription:
    job_id: str
    transcription: str
    filename: str | None = None
    total_duration: float | None = None
    running_time: float = 0.0
    creation_date: datetime = field(default_factory=datetime.utcnow)
