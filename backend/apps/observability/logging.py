import json
import logging

from django.utils.timezone import now

from .context import get_correlation_id


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if hasattr(record, "extra_data"):
            payload["extra"] = record.extra_data
        return json.dumps(payload)
