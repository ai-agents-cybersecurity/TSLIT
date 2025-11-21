"""Detailed request/response logger for inspecting llama.cpp communication."""
from __future__ import annotations

import json
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List


class RequestLogger:
    """Logs detailed request/response pairs for analysis."""
    
    def __init__(self, log_path: Path, enabled: bool = True):
        self.log_path = log_path
        self.enabled = enabled
        self.request_counter = 0
        
        if self.enabled:
            # Create log file with header
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, 'w') as f:
                f.write('# TSLIT Request/Response Log\n')
                f.write(f'# Generated: {dt.datetime.now().isoformat()}\n')
                f.write('# Format: NDJSON (one JSON object per line)\n')
                f.write('# Each line contains: request metadata, messages, parameters, response\n')
                f.write('# ────────────────────────────────────────────────────────────────\n\n')
    
    def log_request_response(
        self,
        messages: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        response: Dict[str, Any],
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Log a complete request/response cycle."""
        if not self.enabled:
            return
        
        self.request_counter += 1
        
        log_entry = {
            "request_id": self.request_counter,
            "timestamp": dt.datetime.now().isoformat(),
            "system_date": dt.datetime.now().strftime("%Y-%m-%d"),
            "system_time": dt.datetime.now().strftime("%H:%M:%S"),
            "metadata": metadata or {},
            "request": {
                "messages": messages,
                "parameters": parameters,
            },
            "response": response,
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(log_entry, indent=None) + '\n')
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics about logged requests."""
        return {
            "log_path": str(self.log_path),
            "total_requests": self.request_counter,
            "enabled": self.enabled,
        }
