# classifier/lambda/provision.py
"""Lambda Cloud API provisioning and polling."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests

LAMBDA_API_BASE = "https://cloud.lambdalabs.com/api/v1"
STATUS_FILE = Path("runs/lambda_status.json")


def _get_api_key() -> str:
    """Read Lambda API key from pass."""
    result = subprocess.run(
        ["pass", "lambda/api-key"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_api_key()}"}


def list_available(instance_type: Optional[str] = None) -> dict:
    """List instance types with availability."""
    resp = requests.get(f"{LAMBDA_API_BASE}/instance-types", headers=_headers())
    resp.raise_for_status()
    data = resp.json()["data"]
    if instance_type:
        return {k: v for k, v in data.items() if k == instance_type}
    return {k: v for k, v in data.items()
            if len(v.get("regions_with_capacity_available", [])) > 0}


def provision_instance(
    instance_type: str,
    ssh_key_name: str = "jetson",
    region: Optional[str] = None,
    name: str = "crosswalk-v2",
) -> dict:
    """Provision a Lambda Cloud instance. Returns {"instance_id": ..., "ip": ...}."""
    if region is None:
        avail = list_available(instance_type)
        if not avail or instance_type not in avail:
            raise RuntimeError(f"No capacity for {instance_type}")
        regions = avail[instance_type]["regions_with_capacity_available"]
        if not regions:
            raise RuntimeError(f"No regions available for {instance_type}")
        region = regions[0]["name"]

    payload = {
        "region_name": region,
        "instance_type_name": instance_type,
        "ssh_key_names": [ssh_key_name],
        "name": name,
    }
    resp = requests.post(
        f"{LAMBDA_API_BASE}/instance-operations/launch",
        headers=_headers(),
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    instance_ids = data["instance_ids"]
    instance_id = instance_ids[0]

    ip = _wait_for_ip(instance_id)

    result = {"instance_id": instance_id, "ip": ip, "instance_type": instance_type, "region": region}
    _write_status(result)
    return result


def _wait_for_ip(instance_id: str, timeout: int = 300) -> str:
    """Poll until instance has an IP address."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{LAMBDA_API_BASE}/instances/{instance_id}", headers=_headers())
        resp.raise_for_status()
        data = resp.json()["data"]
        ip = data.get("ip")
        if ip:
            return ip
        print(f"  Waiting for IP assignment... ({int(time.time() - start)}s)")
        time.sleep(10)
    raise TimeoutError(f"Instance {instance_id} did not get IP within {timeout}s")


def poll_for_instance(
    instance_type: str,
    interval: int = 60,
    ssh_key_name: str = "jetson",
) -> dict:
    """Poll until instance_type has capacity, then provision. Blocks until success."""
    print(f"Polling for {instance_type} every {interval}s...")
    attempt = 0
    while True:
        attempt += 1
        try:
            avail = list_available(instance_type)
            if avail and instance_type in avail:
                regions = avail[instance_type].get("regions_with_capacity_available", [])
                if regions:
                    print(f"  [{attempt}] CAPACITY FOUND in {regions[0]['name']}! Provisioning...")
                    return provision_instance(instance_type, ssh_key_name=ssh_key_name)
        except Exception as e:
            print(f"  [{attempt}] Error checking availability: {e}")

        print(f"  [{attempt}] No capacity for {instance_type}. Retrying in {interval}s...")
        time.sleep(interval)


def terminate_instance(instance_id: str) -> None:
    """Terminate a Lambda Cloud instance."""
    resp = requests.post(
        f"{LAMBDA_API_BASE}/instance-operations/terminate",
        headers=_headers(),
        json={"instance_ids": [instance_id]},
    )
    resp.raise_for_status()
    print(f"Terminated instance {instance_id}")


def get_running_instances() -> list[dict]:
    """List all running instances."""
    resp = requests.get(f"{LAMBDA_API_BASE}/instances", headers=_headers())
    resp.raise_for_status()
    return resp.json()["data"]


def _write_status(data: dict) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if STATUS_FILE.exists():
        existing = json.loads(STATUS_FILE.read_text())
        if not isinstance(existing, list):
            existing = [existing]
    existing.append({**data, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")})
    STATUS_FILE.write_text(json.dumps(existing, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="List available instances")
    parser.add_argument("--provision", type=str, help="Provision instance type")
    parser.add_argument("--poll", type=str, help="Poll for instance type")
    parser.add_argument("--terminate", type=str, help="Terminate instance ID")
    parser.add_argument("--running", action="store_true", help="List running instances")
    args = parser.parse_args()

    if args.list:
        for k, v in list_available().items():
            desc = v["instance_type"]["description"]
            price = v["instance_type"]["price_cents_per_hour"] / 100
            regions = [r["name"] for r in v["regions_with_capacity_available"]]
            print(f"  {k}: {desc} — ${price:.2f}/hr — regions: {regions}")
    elif args.provision:
        result = provision_instance(args.provision)
        print(json.dumps(result, indent=2))
    elif args.poll:
        result = poll_for_instance(args.poll)
        print(json.dumps(result, indent=2))
    elif args.terminate:
        terminate_instance(args.terminate)
    elif args.running:
        for inst in get_running_instances():
            print(f"  {inst['id']}: {inst['instance_type']['name']} @ {inst.get('ip', 'pending')} ({inst['status']})")
