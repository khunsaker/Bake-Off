#!/usr/bin/env python3
"""
Locust Load Test for Shark Bake-Off
Supports multiple workload patterns and realistic query distributions
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser

# Sample test data
MODE_S_IDS = [
    "A12345", "A67890", "B12345", "C98765", "D11111",
    "E22222", "F33333", "G44444", "H55555", "I66666",
] * 10  # Multiply for more variety

MMSI_IDS = [
    "366123456", "366234567", "366345678", "235987654", "235876543",
    "311234567", "311345678", "303456789", "257123456", "257234567",
] * 10

COUNTRIES = [
    "USA", "China", "Russia", "United Kingdom", "France",
    "Germany", "Japan", "India", "Italy", "Canada",
]


class SharkBakeOffUser(FastHttpUser):
    """
    Base user for Shark Bake-Off benchmarks

    Uses FastHttpUser for better performance (uses gevent and C-based HTTP client)
    """

    # Wait time between requests (simulates think time)
    wait_time = between(0.1, 0.5)  # 100-500ms

    @task(95)  # 95% weight - most common query
    def lookup_aircraft(self):
        """S1: Simple aircraft lookup by Mode-S"""
        mode_s = random.choice(MODE_S_IDS)
        with self.client.get(
            f"/api/aircraft/mode_s/{mode_s}",
            name="/api/aircraft/mode_s/[mode_s]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Not found is acceptable for test data
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(95)
    def lookup_ship(self):
        """S1: Simple ship lookup by MMSI"""
        mmsi = random.choice(MMSI_IDS)
        with self.client.get(
            f"/api/ship/mmsi/{mmsi}",
            name="/api/ship/mmsi/[mmsi]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(4)
    def two_hop_query(self):
        """S3: Two-hop traversal query"""
        country = random.choice(COUNTRIES)
        with self.client.get(
            f"/api/aircraft/country/{country}",
            name="/api/aircraft/country/[country]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(4)
    def three_hop_query(self):
        """S6: Three-hop cross-domain query"""
        country = random.choice(COUNTRIES)
        with self.client.get(
            f"/api/cross-domain/country/{country}",
            name="/api/cross-domain/country/[country]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def activity_history(self):
        """S11: Activity history query"""
        mmsi = random.choice(MMSI_IDS)
        with self.client.get(
            f"/api/activity/mmsi/{mmsi}",
            name="/api/activity/mmsi/[mmsi]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def log_activity(self):
        """Activity logging (write operation)"""
        payload = {
            "track_id": f"LOCUST-{random.randint(10000, 99999)}",
            "event_type": "activity_detected",
            "domain": random.choice(["AIR", "MARITIME"]),
            "mode_s": random.choice(MODE_S_IDS) if random.random() > 0.5 else None,
            "mmsi": random.choice(MMSI_IDS) if random.random() > 0.5 else None,
            "activity_type": "load_test",
            "latitude": 35.0 + random.uniform(-5, 5),
            "longitude": -118.0 + random.uniform(-5, 5),
            "properties": {"test": True},
        }

        with self.client.post(
            "/api/activity/log",
            name="/api/activity/log",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class LookupHeavyUser(FastHttpUser):
    """
    Lookup-heavy workload (95/4/1)
    Simulates high-frequency identifier lookups
    """
    wait_time = between(0.01, 0.1)  # Fast queries

    @task(95)
    def lookup_aircraft(self):
        mode_s = random.choice(MODE_S_IDS)
        self.client.get(f"/api/aircraft/mode_s/{mode_s}", name="/api/aircraft/mode_s/[mode_s]")

    @task(4)
    def analytics_query(self):
        country = random.choice(COUNTRIES)
        self.client.get(f"/api/aircraft/country/{country}", name="/api/aircraft/country/[country]")

    @task(1)
    def write_activity(self):
        payload = {
            "track_id": f"LOCUST-{random.randint(10000, 99999)}",
            "event_type": "activity_detected",
            "domain": "AIR",
            "mode_s": random.choice(MODE_S_IDS),
            "activity_type": "load_test",
        }
        self.client.post("/api/activity/log", json=payload, name="/api/activity/log")


class AnalyticsHeavyUser(FastHttpUser):
    """
    Analytics-heavy workload (20/70/10)
    Simulates complex query patterns
    """
    wait_time = between(0.5, 2.0)  # Slower, more complex queries

    @task(20)
    def lookup_query(self):
        mode_s = random.choice(MODE_S_IDS)
        self.client.get(f"/api/aircraft/mode_s/{mode_s}", name="/api/aircraft/mode_s/[mode_s]")

    @task(35)
    def two_hop_query(self):
        country = random.choice(COUNTRIES)
        self.client.get(f"/api/aircraft/country/{country}", name="/api/aircraft/country/[country]")

    @task(35)
    def three_hop_query(self):
        country = random.choice(COUNTRIES)
        self.client.get(f"/api/cross-domain/country/{country}", name="/api/cross-domain/country/[country]")

    @task(10)
    def activity_query(self):
        mmsi = random.choice(MMSI_IDS)
        self.client.get(f"/api/activity/mmsi/{mmsi}", name="/api/activity/mmsi/[mmsi]")


class BalancedUser(FastHttpUser):
    """
    Balanced workload (50/40/10)
    Realistic mixed usage
    """
    wait_time = between(0.1, 0.5)

    @task(50)
    def lookup_queries(self):
        if random.random() > 0.5:
            mode_s = random.choice(MODE_S_IDS)
            self.client.get(f"/api/aircraft/mode_s/{mode_s}", name="/api/aircraft/mode_s/[mode_s]")
        else:
            mmsi = random.choice(MMSI_IDS)
            self.client.get(f"/api/ship/mmsi/{mmsi}", name="/api/ship/mmsi/[mmsi]")

    @task(40)
    def analytics_queries(self):
        country = random.choice(COUNTRIES)
        if random.random() > 0.5:
            self.client.get(f"/api/aircraft/country/{country}", name="/api/aircraft/country/[country]")
        else:
            self.client.get(f"/api/cross-domain/country/{country}", name="/api/cross-domain/country/[country]")

    @task(10)
    def write_operations(self):
        payload = {
            "track_id": f"LOCUST-{random.randint(10000, 99999)}",
            "event_type": "activity_detected",
            "domain": random.choice(["AIR", "MARITIME"]),
            "mode_s": random.choice(MODE_S_IDS) if random.random() > 0.5 else None,
            "mmsi": random.choice(MMSI_IDS) if random.random() > 0.5 else None,
            "activity_type": "load_test",
        }
        self.client.post("/api/activity/log", json=payload, name="/api/activity/log")


# Event hooks for custom metrics
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize custom metrics"""
    print("="*70)
    print("Shark Bake-Off Load Test Starting")
    print("="*70)
    print(f"Target: {environment.host}")
    print("="*70)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary on test stop"""
    print("\n" + "="*70)
    print("Load Test Complete")
    print("="*70)
    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests:,}")
    print(f"Total Failures: {stats.total.num_failures:,}")
    print(f"Average RPS: {stats.total.current_rps:.2f}")
    print(f"Median Response Time: {stats.total.median_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print("="*70 + "\n")
