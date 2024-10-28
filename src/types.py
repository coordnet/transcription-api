from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Type for transcriptions in the database
@dataclass
class Transcription:
    job_id: str
    transcription: str
    filename: Optional[str] = None
    total_duration: Optional[float] = None
    running_time: float = 0.0
    creation_date: datetime = field(default_factory=datetime.utcnow)
