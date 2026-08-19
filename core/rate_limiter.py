import time
import random
import threading
import json
import os

class RateLimiter:
    def __init__(self, rpm=30, burst=5, log_path="logs/rate_limits.jsonl"):
        self.rpm = rpm
        self.burst = burst
        self.bucket = float(burst)
        self.last_refill = time.time()
        self.backoff_multiplier = 1.0
        self.max_backoff = 30.0
        self.lock = threading.Lock()
        self.log_path = log_path
        self.events = []
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.bucket = min(self.burst, self.bucket + elapsed * (self.rpm / 60.0))
        self.last_refill = now

    def wait(self):
        with self.lock:
            self._refill()
            if self.bucket < 1:
                wait_time = (1.0 - self.bucket) * (60.0 / self.rpm) * self.backoff_multiplier
                jitter = random.uniform(0.5, 1.5)
                actual_wait = wait_time * jitter
                event = {
                    "timestamp": time.time(),
                    "event": "rate_limit_wait",
                    "wait_seconds": round(actual_wait, 2),
                    "backoff_multiplier": round(self.backoff_multiplier, 2),
                    "bucket_level": round(self.bucket, 2)
                }
                self.events.append(event)
                self._log_event(event)
                time.sleep(actual_wait)
                self.backoff_multiplier = min(self.backoff_multiplier * 2.0, self.max_backoff)
                self._refill()
                self.bucket -= 1
            else:
                self.bucket -= 1
                self.backoff_multiplier = max(1.0, self.backoff_multiplier * 0.85)

    def _log_event(self, event):
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass

    def stats(self):
        return {
            "total_events": len(self.events),
            "total_wait_seconds": round(sum(e["wait_seconds"] for e in self.events), 2),
            "max_backoff_reached": round(max((e["backoff_multiplier"] for e in self.events), default=1.0), 2),
            "current_bucket": round(self.bucket, 2),
            "current_backoff": round(self.backoff_multiplier, 2)
        }

    def reset_backoff(self):
        with self.lock:
            self.backoff_multiplier = 1.0
