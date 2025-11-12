"""
Rate Limiting Test Data Factory

Generates test scenarios for rate limiting, burst traffic,
and throttling behavior in CI/CD API integrations.
"""

import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker

fake = Faker()


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""

    requests_per_second: int = 10
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_size: int = 20
    window_size_seconds: int = 60


@dataclass
class RequestEvent:
    """Single request event for rate limit testing"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    endpoint: str = "/api/v1/test"
    method: str = "GET"
    client_id: str = field(default_factory=fake.user_name)
    ip_address: str = field(default_factory=fake.ipv4)
    user_agent: str = field(default_factory=fake.user_agent)
    response_code: int = 200
    response_time_ms: float = 0.0


class RateLimitFactory:
    """Factory for rate limit test scenarios"""

    @staticmethod
    def create_normal_traffic(
        duration_seconds: int = 60,
        requests_per_second: int = 5,
    ) -> List[RequestEvent]:
        """Generate normal traffic pattern"""
        events = []
        start_time = time.time()

        for second in range(duration_seconds):
            for _ in range(requests_per_second):
                timestamp = start_time + second + random.uniform(0, 0.99)
                events.append(
                    RequestEvent(
                        timestamp=timestamp,
                        response_time_ms=random.uniform(10, 100),
                    )
                )

        return sorted(events, key=lambda e: e.timestamp)

    @staticmethod
    def create_burst_traffic(
        burst_count: int = 100,
        burst_duration_seconds: float = 1.0,
    ) -> List[RequestEvent]:
        """Generate burst traffic scenario"""
        events = []
        start_time = time.time()

        for i in range(burst_count):
            timestamp = start_time + (i / burst_count) * burst_duration_seconds
            events.append(
                RequestEvent(
                    timestamp=timestamp,
                    response_code=429 if i > 20 else 200,  # Rate limit after 20 requests
                    response_time_ms=random.uniform(5, 50) if i <= 20 else random.uniform(100, 200),
                )
            )

        return sorted(events, key=lambda e: e.timestamp)

    @staticmethod
    def create_gradual_increase(
        duration_seconds: int = 300,
        start_rps: int = 1,
        end_rps: int = 50,
    ) -> List[RequestEvent]:
        """Generate gradually increasing traffic"""
        events = []
        start_time = time.time()

        for second in range(duration_seconds):
            rps = start_rps + ((end_rps - start_rps) * second / duration_seconds)
            for _ in range(int(rps)):
                timestamp = start_time + second + random.uniform(0, 0.99)

                # Simulate rate limiting after threshold
                response_code = 429 if rps > 30 else 200

                events.append(
                    RequestEvent(
                        timestamp=timestamp,
                        response_code=response_code,
                        response_time_ms=random.uniform(10, 100) if response_code == 200 else random.uniform(50, 200),
                    )
                )

        return sorted(events, key=lambda e: e.timestamp)

    @staticmethod
    def create_spike_pattern(
        duration_seconds: int = 60,
        spike_count: int = 3,
        spike_duration: float = 2.0,
    ) -> List[RequestEvent]:
        """Generate traffic with periodic spikes"""
        events = []
        start_time = time.time()
        spike_interval = duration_seconds / spike_count

        for second in range(duration_seconds):
            # Check if we're in a spike period
            is_spike = any(
                abs((second - i * spike_interval) % spike_interval) < spike_duration
                for i in range(spike_count)
            )

            rps = 50 if is_spike else 5

            for _ in range(rps):
                timestamp = start_time + second + random.uniform(0, 0.99)
                events.append(
                    RequestEvent(
                        timestamp=timestamp,
                        response_code=429 if is_spike and random.random() > 0.5 else 200,
                    )
                )

        return sorted(events, key=lambda e: e.timestamp)


class BurstScenarioFactory:
    """Factory for specific burst test scenarios"""

    @staticmethod
    def create_webhook_flood(count: int = 100) -> List[Dict[str, Any]]:
        """Generate webhook flood scenario"""
        return [
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "push",
                "timestamp": time.time() + (i * 0.01),  # 100 events in 1 second
                "payload": {
                    "repository": fake.slug(),
                    "commits": [{"id": fake.sha256()[:40]}],
                },
            }
            for i in range(count)
        ]

    @staticmethod
    def create_parallel_uploads(
        file_count: int = 50,
        file_size_mb: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """Generate parallel artifact upload scenario"""
        start_time = time.time()
        return [
            {
                "upload_id": str(uuid.uuid4()),
                "filename": f"artifact-{i}.zip",
                "size_bytes": int(file_size_mb * 1024 * 1024),
                "start_time": start_time + random.uniform(0, 2),
                "chunk_size": 1048576,  # 1MB chunks
                "chunks": int(file_size_mb),
            }
            for i in range(file_count)
        ]

    @staticmethod
    def create_ci_trigger_storm(
        pipeline_count: int = 20,
    ) -> List[Dict[str, Any]]:
        """Generate CI pipeline trigger storm"""
        return [
            {
                "trigger_id": str(uuid.uuid4()),
                "pipeline": f"pipeline-{i}",
                "trigger_type": random.choice(["push", "pull_request", "manual", "schedule"]),
                "timestamp": time.time() + random.uniform(0, 5),
                "branch": random.choice(["main", "develop", f"feature/branch-{i}"]),
            }
            for i in range(pipeline_count)
        ]


class ThrottleScenarioFactory:
    """Factory for throttling test scenarios"""

    @staticmethod
    def create_sliding_window_test(
        window_size: int = 60,
        limit: int = 100,
        test_requests: int = 150,
    ) -> List[Dict[str, Any]]:
        """Generate sliding window rate limit test"""
        events = []
        start_time = time.time()

        for i in range(test_requests):
            timestamp = start_time + (i / test_requests) * window_size

            # Calculate how many requests in the window
            requests_in_window = sum(
                1 for e in events
                if e["timestamp"] > timestamp - window_size
            )

            events.append({
                "request_id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "requests_in_window": requests_in_window,
                "allowed": requests_in_window < limit,
                "response_code": 200 if requests_in_window < limit else 429,
            })

        return events

    @staticmethod
    def create_token_bucket_test(
        bucket_size: int = 100,
        refill_rate: int = 10,  # tokens per second
        duration: int = 60,
    ) -> List[Dict[str, Any]]:
        """Generate token bucket algorithm test"""
        events = []
        start_time = time.time()
        tokens = bucket_size

        for second in range(duration):
            # Refill tokens
            tokens = min(tokens + refill_rate, bucket_size)

            # Generate requests
            requests_this_second = random.randint(5, 20)

            for _ in range(requests_this_second):
                timestamp = start_time + second + random.uniform(0, 0.99)

                if tokens > 0:
                    tokens -= 1
                    allowed = True
                    response_code = 200
                else:
                    allowed = False
                    response_code = 429

                events.append({
                    "request_id": str(uuid.uuid4()),
                    "timestamp": timestamp,
                    "tokens_available": tokens,
                    "allowed": allowed,
                    "response_code": response_code,
                })

        return sorted(events, key=lambda e: e["timestamp"])

    @staticmethod
    def create_leaky_bucket_test(
        bucket_size: int = 100,
        leak_rate: int = 10,  # requests per second
        duration: int = 60,
    ) -> List[Dict[str, Any]]:
        """Generate leaky bucket algorithm test"""
        events = []
        start_time = time.time()
        queue_size = 0

        for second in range(duration):
            # Leak from bucket
            queue_size = max(0, queue_size - leak_rate)

            # Generate requests
            requests_this_second = random.randint(5, 20)

            for _ in range(requests_this_second):
                timestamp = start_time + second + random.uniform(0, 0.99)

                if queue_size < bucket_size:
                    queue_size += 1
                    allowed = True
                    response_code = 202  # Accepted, will be processed
                else:
                    allowed = False
                    response_code = 429  # Bucket overflow

                events.append({
                    "request_id": str(uuid.uuid4()),
                    "timestamp": timestamp,
                    "queue_size": queue_size,
                    "allowed": allowed,
                    "response_code": response_code,
                })

        return sorted(events, key=lambda e: e["timestamp"])


# Rate limit response factory
class RateLimitResponseFactory:
    """Factory for rate limit API responses"""

    @staticmethod
    def create_rate_limit_headers(
        limit: int = 100,
        remaining: int = 50,
        reset_timestamp: Optional[int] = None,
    ) -> Dict[str, str]:
        """Generate rate limit headers"""
        reset_timestamp = reset_timestamp or int(time.time()) + 3600

        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_timestamp),
            "X-RateLimit-Window": "3600",
        }

    @staticmethod
    def create_rate_limit_error() -> Dict[str, Any]:
        """Generate rate limit error response"""
        retry_after = random.randint(60, 3600)
        return {
            "error": {
                "type": "rate_limit_exceeded",
                "message": "Rate limit exceeded. Please retry after the specified time.",
                "code": "RATE_LIMIT_429",
                "retry_after": retry_after,
                "retry_after_human": f"{retry_after // 60} minutes",
            },
            "status": 429,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_throttle_response() -> Dict[str, Any]:
        """Generate throttle response"""
        return {
            "error": {
                "type": "throttled",
                "message": "Request throttled due to high load.",
                "code": "THROTTLE_503",
                "retry_after": random.randint(5, 60),
            },
            "status": 503,
            "timestamp": datetime.utcnow().isoformat(),
        }
