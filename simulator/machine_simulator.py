#!/usr/bin/env python3
"""Machine sensor data simulator for SmartMaintain AI."""

import argparse
import asyncio
import json
import logging
import math
import random
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MACHINES = [
    {"machineId": "MOTOR-204", "type": "motor", "base_temp": 71, "base_vib": 2.4},
    {"machineId": "PUMP-107", "type": "pump", "base_temp": 64, "base_vib": 1.9},
    {"machineId": "CONV-301", "type": "conveyor", "base_temp": 57, "base_vib": 1.7},
    {"machineId": "CNC-512", "type": "cnc", "base_temp": 54, "base_vib": 1.1},
    {"machineId": "COMP-089", "type": "compressor", "base_temp": 76, "base_vib": 2.8},
]


class Scenario(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    FAILURE = "failure"
    BEARING_FAILURE = "bearing_failure"


class MachineSimulator:
    def __init__(self, machine: dict, scenario: Scenario = Scenario.NORMAL):
        self.machine = machine
        self.scenario = scenario
        self.tick = 0
        self.failed = False

    def generate_reading(self) -> dict:
        self.tick += 1
        m = self.machine
        noise = lambda s: random.gauss(0, s)

        temp = m["base_temp"] + noise(0.5)
        vib = m["base_vib"] + abs(noise(0.1))
        pressure = 40 + random.uniform(-3, 3)
        power = 13 + random.uniform(-1, 1)
        speed = 1750 + random.uniform(-20, 20)
        load = 70 + random.uniform(-5, 5)

        if self.scenario in (Scenario.WARNING, Scenario.FAILURE, Scenario.BEARING_FAILURE):
            progress = min(self.tick / 60, 1.0)
            vib += progress * 2.5
            temp += progress * 15
            speed -= progress * 100
            power += progress * 5
            load += progress * 10

        if self.scenario == Scenario.FAILURE and self.tick > 80:
            self.failed = True
            vib += 5
            temp += 20
            speed = max(0, speed - 200)

        if self.scenario == Scenario.BEARING_FAILURE and self.tick > 50:
            vib += math.sin(self.tick / 5) * 1.5 + self.tick * 0.05
            temp += self.tick * 0.2

        return {
            "machineId": m["machineId"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": round(temp, 1),
            "vibration": round(max(0, vib), 2),
            "pressure": round(pressure, 1),
            "powerConsumption": round(power, 1),
            "rotationalSpeed": round(max(0, speed), 0),
            "operatingLoad": round(min(100, load), 1),
        }


async def publish_http(reading: dict, api_url: str, token: Optional[str]) -> bool:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {k: v for k, v in reading.items() if k != "timestamp"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(f"{api_url}/api/readings", json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                pred = data.get("prediction", {})
                alert = data.get("alert")
                logger.info(
                    "%s | temp=%.1f vib=%.2f | health=%.0f fail=%.0f%% %s",
                    reading["machineId"],
                    reading["temperature"],
                    reading["vibration"],
                    pred.get("healthScore", 0),
                    pred.get("failureProbability", 0) * 100,
                    f"ALERT: {alert['severity']}" if alert else "",
                )
                return True
            logger.warning("HTTP %s for %s", resp.status_code, reading["machineId"])
        except Exception as exc:
            logger.error("Failed to publish %s: %s", reading["machineId"], exc)
    return False


async def get_auth_token(api_url: str, email: str, password: str) -> Optional[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                f"{api_url}/api/auth/login",
                json={"email": email, "password": password},
            )
            if resp.status_code == 200:
                return resp.json()["access_token"]
        except Exception as exc:
            logger.error("Auth failed: %s", exc)
    return None


async def run_simulator(
    api_url: str = "http://localhost:8080",
    interval: float = 5.0,
    scenario: Scenario = Scenario.NORMAL,
    target_machine: Optional[str] = None,
    email: str = "operator@smartmaintain.ai",
    password: str = "demo123",
):
    token = await get_auth_token(api_url, email, password)
    if not token:
        logger.error("Could not authenticate. Is the backend running?")
        sys.exit(1)

    simulators = []
    for m in MACHINES:
        sc = scenario if (target_machine is None or m["machineId"] == target_machine) else Scenario.NORMAL
        simulators.append(MachineSimulator(m, sc))

    logger.info(
        "Starting simulator: %d machines, interval=%ss, scenario=%s",
        len(simulators),
        interval,
        scenario.value,
    )

    while True:
        tasks = []
        for sim in simulators:
            if sim.failed and sim.scenario == Scenario.FAILURE:
                continue
            reading = sim.generate_reading()
            tasks.append(publish_http(reading, api_url, token))
        await asyncio.gather(*tasks)
        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="SmartMaintain AI Sensor Simulator")
    parser.add_argument("--api-url", default="http://localhost:8080", help="Backend API URL")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between readings")
    parser.add_argument(
        "--scenario",
        choices=[s.value for s in Scenario],
        default="normal",
        help="Simulation scenario",
    )
    parser.add_argument("--machine", help="Target machine ID for failure scenario (e.g. MOTOR-204)")
    parser.add_argument("--email", default="operator@smartmaintain.ai")
    parser.add_argument("--password", default="demo123")
    args = parser.parse_args()

    asyncio.run(
        run_simulator(
            api_url=args.api_url,
            interval=args.interval,
            scenario=Scenario(args.scenario),
            target_machine=args.machine,
            email=args.email,
            password=args.password,
        )
    )


if __name__ == "__main__":
    main()
