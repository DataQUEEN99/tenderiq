from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass
class DomainEvent:
    event_type: str
    aggregate_id: str
    organization_id: str
    user_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }