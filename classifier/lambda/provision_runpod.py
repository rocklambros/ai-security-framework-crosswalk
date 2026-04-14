# classifier/lambda/provision_runpod.py
"""RunPod API provisioning: create pod, poll for SSH, terminate."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests

GRAPHQL_URL = "https://api.runpod.io/graphql"
STATUS_FILE = Path("runs/runpod_status.json")

# GPU preference order: fastest first
GPU_PREFERENCE = [
    "NVIDIA H100 80GB HBM3",   # H100 SXM
    "NVIDIA H100 NVL",         # H100 NVL 94GB
    "NVIDIA H100 PCIe",        # H100 PCIe
    "NVIDIA A100-SXM4-80GB",   # A100 SXM
    "NVIDIA A100 80GB PCIe",   # A100 PCIe
]


def _get_api_key() -> str:
    result = subprocess.run(
        ["pass", "runpod/api-key"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def _gql(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query against RunPod API."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(
        GRAPHQL_URL,
        headers={"Authorization": f"Bearer {_get_api_key()}", "Content-Type": "application/json"},
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data and data["errors"]:
        # Filter out non-critical errors (like lowestPrice internal errors)
        critical = [e for e in data["errors"] if "lowestPrice" not in str(e.get("path", []))]
        if critical:
            raise RuntimeError(f"GraphQL errors: {critical}")
    return data.get("data", {})


def list_available_gpus() -> list[dict]:
    """List GPU types with availability."""
    data = _gql("query { gpuTypes { id displayName memoryInGb secureCloud communityCloud } }")
    return data.get("gpuTypes", [])


def find_fastest_available(min_vram_gb: int = 80) -> str:
    """Find the fastest available GPU with at least min_vram_gb VRAM."""
    gpus = list_available_gpus()
    available_ids = set()
    for g in gpus:
        if (g.get("memoryInGb") or 0) >= min_vram_gb:
            if g.get("communityCloud") or g.get("secureCloud"):
                available_ids.add(g["id"])

    for pref in GPU_PREFERENCE:
        if pref in available_ids:
            return pref

    # Fallback: largest VRAM available
    big = [g for g in gpus if g["id"] in available_ids]
    if big:
        big.sort(key=lambda g: -(g.get("memoryInGb") or 0))
        return big[0]["id"]

    raise RuntimeError(f"No GPU with >= {min_vram_gb}GB VRAM available")


def create_pod(
    gpu_type_id: str,
    name: str = "crosswalk-v7",
    image: str = "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
    gpu_count: int = 1,
    volume_gb: int = 100,
    container_disk_gb: int = 50,
    cloud_type: str = "SECURE",
) -> dict:
    """Create a RunPod pod. Returns {pod_id, ip, port, gpu_type, status}.

    Tries SECURE first, falls back to COMMUNITY if unavailable.
    """
    for ct in ([cloud_type] if cloud_type != "ALL" else ["SECURE", "COMMUNITY"]):
        payload = {
            "name": name,
            "imageName": image,
            "gpuTypeIds": [gpu_type_id],
            "gpuCount": gpu_count,
            "cloudType": ct,
            "volumeInGb": volume_gb,
            "containerDiskInGb": container_disk_gb,
            "ports": ["22/tcp"],
            "supportPublicIp": True,
        }
        resp = requests.post(
            "https://rest.runpod.io/v1/pods",
            headers={"Authorization": f"Bearer {_get_api_key()}", "Content-Type": "application/json"},
            json=payload,
        )
        data = resp.json()
        if isinstance(data, dict) and data.get("id"):
            pod = data
            break
        # If list with error, try next cloud type
        err = data[0]["error"] if isinstance(data, list) else data.get("error", "")
        print(f"  {ct}: {err}")
    else:
        raise RuntimeError(f"Failed to create pod on any cloud type: {data}")

    pod_id = pod["id"]
    print(f"  Pod created: {pod_id} ({gpu_type_id})")
    print(f"  Waiting for SSH to become available...")

    # Poll until we get SSH connection info
    ssh_info = _wait_for_ssh(pod_id)

    result = {
        "pod_id": pod_id,
        "ip": ssh_info["ip"],
        "port": ssh_info["port"],
        "gpu_type": gpu_type_id,
        "status": "RUNNING",
    }
    _write_status(result)
    return result


def _wait_for_ssh(pod_id: str, timeout: int = 600) -> dict:
    """Poll until pod has SSH connection info. Returns {ip, port}.

    Uses REST API portMappings field (populated before runtime).
    """
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"https://rest.runpod.io/v1/pods/{pod_id}",
            headers={"Authorization": f"Bearer {_get_api_key()}"},
        )
        resp.raise_for_status()
        pod = resp.json()
        ip = pod.get("publicIp", "")
        port_mappings = pod.get("portMappings", {})
        ssh_port = port_mappings.get("22")
        if ip and ssh_port:
            # Verify SSH is actually reachable
            import socket
            try:
                s = socket.create_connection((ip, int(ssh_port)), timeout=5)
                s.close()
                return {"ip": ip, "port": int(ssh_port)}
            except (OSError, socket.timeout):
                pass
        elapsed = int(time.time() - start)
        status = pod.get("desiredStatus", "unknown")
        print(f"  [{elapsed}s] Pod {pod_id}: {status}, ip={ip or 'pending'}, ssh_port={ssh_port or 'pending'}...")
        time.sleep(15)

    raise TimeoutError(f"Pod {pod_id} SSH not ready within {timeout}s")


def get_pod(pod_id: str) -> dict:
    """Get pod status."""
    query = """
    query pod($podId: String!) {
        pod(input: { podId: $podId }) {
            id desiredStatus
            runtime {
                uptimeInSeconds
                ports { ip isIpPublic privatePort publicPort }
                gpus { id }
            }
        }
    }
    """
    data = _gql(query, {"podId": pod_id})
    return data.get("pod", {})


def get_running_pods() -> list[dict]:
    """List all running pods."""
    data = _gql("query { myself { pods { id name desiredStatus runtime { ports { ip publicPort privatePort } } machine { gpuDisplayName } } } }")
    myself = data.get("myself", {})
    return [p for p in myself.get("pods", []) if p.get("desiredStatus") == "RUNNING"]


def terminate_pod(pod_id: str) -> None:
    """Terminate a RunPod pod."""
    mutation = """
    mutation terminatePod($input: PodTerminateInput!) {
        podTerminate(input: $input)
    }
    """
    _gql(mutation, {"input": {"podId": pod_id}})
    print(f"  Terminated pod {pod_id}")


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
    parser = argparse.ArgumentParser(description="RunPod provisioner")
    parser.add_argument("--list", action="store_true", help="List available GPUs")
    parser.add_argument("--fastest", action="store_true", help="Find fastest available GPU")
    parser.add_argument("--create", type=str, help="Create pod with GPU type ID")
    parser.add_argument("--running", action="store_true", help="List running pods")
    parser.add_argument("--terminate", type=str, help="Terminate pod ID")
    parser.add_argument("--terminate-all", action="store_true", help="Terminate all pods")
    args = parser.parse_args()

    if args.list:
        for g in list_available_gpus():
            if (g.get("memoryInGb") or 0) >= 48:
                cc = "comm" if g.get("communityCloud") else ""
                sc = "secure" if g.get("secureCloud") else ""
                print(f"  {g['id']:<36} {g['memoryInGb']:>4}GB  {cc} {sc}")
    elif args.fastest:
        gpu = find_fastest_available()
        print(f"Fastest available: {gpu}")
    elif args.create:
        result = create_pod(args.create)
        print(json.dumps(result, indent=2))
    elif args.running:
        for pod in get_running_pods():
            ports = pod.get("runtime", {}).get("ports", [])
            ssh_port = next((p for p in ports if p.get("privatePort") == 22), {})
            ip = ssh_port.get("ip", "pending")
            port = ssh_port.get("publicPort", "?")
            gpu = pod.get("machine", {}).get("gpuDisplayName", "?")
            print(f"  {pod['id']}: {gpu} @ {ip}:{port} ({pod['desiredStatus']})")
    elif args.terminate:
        terminate_pod(args.terminate)
    elif args.terminate_all:
        for pod in get_running_pods():
            terminate_pod(pod["id"])
