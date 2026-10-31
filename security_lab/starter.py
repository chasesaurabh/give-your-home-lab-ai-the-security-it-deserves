"""Start an owned CPU-only model, evaluate synthetic cases and rehearse recovery.

Requires Python and a running Linux-container Docker engine. No pip dependency.
Reads only synthetic fixtures; never connects to an existing inference service.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import time
from urllib.request import Request

from .model_eval import evaluate_case, run
from .protocol import local_opener, strict_json
from .runner import ROOT, load_fixture

IMAGE = "ollama/ollama:0.40.12@sha256:20d1bbfbabe1c97ba4b16301f08a20d8484bcf77047742a3cb71c613d8e12d0b"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"
MODEL_DIGEST = "0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0"
NAME = "security-lab-starter-model"
NETWORK = "security-lab-starter-network"


def docker(*args, timeout=120):
    # Docker emits UTF-8 progress on stderr. Keep streams as bytes so a Windows
    # locale cannot crash subprocess's reader thread while the command succeeds.
    result = subprocess.run(["docker", *args], capture_output=True, timeout=timeout)
    if result.returncode:
        # No raw daemon diagnostics in public evidence: they may disclose host paths.
        raise RuntimeError("Docker command failed: " + args[0])
    return result.stdout.decode("utf-8").strip()


def get_json(url):
    with local_opener().open(Request(url), timeout=5) as response:
        raw = response.read(1048577)
    if len(raw) > 1048576:
        raise ValueError("Starter metadata response exceeds limit")
    return strict_json(raw)


def wait_ready(origin):
    for _ in range(60):
        try:
            return get_json(origin + "/api/version")
        except (OSError, ValueError):
            time.sleep(.5)
    raise RuntimeError("Owned model server did not become ready")


def start(destination, port=18136, volume="security-lab-starter-models", keep_running=False):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("Use an unprivileged port between 1024 and 65535")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,80}", volume):
        raise ValueError("Use a simple lowercase named Docker volume")
    folder = Path(destination).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        (folder / (name + ".json")).write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")
    record = {"started_utc":datetime.now(timezone.utc).isoformat(), "status":"running",
              "image":IMAGE, "model":MODEL, "python":platform.python_version(),
              "host_os":platform.system(), "host_architecture":platform.machine(),
              "port":port, "volume":volume, "cpus_cap":8, "memory_cap_bytes":6442450944,
              "gpu_requested":False, "context_limit":4096,
              "starter_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    server_id = network_id = None
    origin = f"http://127.0.0.1:{port}"
    try:
        engine = strict_json(docker("info", "--format", "{{json .}}"))
        record["engine"] = {key:engine.get(key) for key in ["ServerVersion","OSType","Architecture","NCPU","MemTotal"]}
        if engine.get("OSType") != "linux":
            raise ValueError("This starter requires Linux containers")
        if docker("ps", "-aq", "--filter", f"name=^/{NAME}$"):
            raise ValueError("Starter container already exists; inspect it before reuse")
        if docker("network", "ls", "-q", "--filter", f"name=^{NETWORK}$"):
            raise ValueError("Starter network already exists; inspect it before reuse")
        record["volume_preexisted"] = bool(docker("volume", "ls", "-q", "--filter", f"name=^{volume}$"))
        save("result", record)
        print("Pulling pinned runtime and preparing owned CPU model server", flush=True)
        docker("pull", IMAGE, timeout=900)
        image = strict_json(docker("image", "inspect", IMAGE))[0]
        save("runtime-image", {key:image.get(key) for key in ["Id","RepoDigests","Architecture","Os","Size"]})
        docker("volume", "create", volume)
        network_id = docker("network", "create", NETWORK)
        # Persist ownership before attempting the next resource acquisition.
        # A create/cleanup failure must not direct the reader to a missing ID.
        record["owned_network_id"] = network_id
        save("result", record)
        server_id = docker("create", "--name", NAME, "--network", NETWORK,
                           "--cpus", "8", "--memory", "6g", "--memory-swap", "6g",
                           "-e", "OLLAMA_NO_CLOUD=1", "-e", "OLLAMA_CONTEXT_LENGTH=4096",
                           "-e", "OLLAMA_NUM_PARALLEL=1", "-p", f"127.0.0.1:{port}:11434",
                           "-v", f"{volume}:/root/.ollama", IMAGE)
        record["owned_container_id"] = server_id
        save("result", record)
        docker("start", server_id)
        details = strict_json(docker("inspect", server_id))[0]
        host = details["HostConfig"]
        save("container-settings", {
            "image_id": details["Image"],
            "port_bindings": host["PortBindings"],
            "memory_limit": host["Memory"], "memory_swap_limit": host["MemorySwap"],
            "nano_cpus": host["NanoCpus"], "device_requests": host.get("DeviceRequests"),
            "privileged": host["Privileged"],
            "mounts": [{key:m.get(key) for key in ["Type", "Name", "Destination", "RW"]}
                       for m in details["Mounts"]],
            "networks": list(details["NetworkSettings"]["Networks"]),
            "starter_environment": [v for v in details["Config"]["Env"]
                                    if v.split("=", 1)[0] in
                                    {"OLLAMA_NO_CLOUD", "OLLAMA_CONTEXT_LENGTH", "OLLAMA_NUM_PARALLEL"}]
        })
        save("runtime-version", wait_ready(origin))
        print("Downloading/checking model files; an empty volume needs about 2.5 GB", flush=True)
        docker("exec", server_id, "ollama", "pull", MODEL, timeout=1800)
        tags = get_json(origin + "/api/tags")
        save("model-tags", tags)
        matches = [x for x in tags.get("models", []) if x.get("name") == MODEL]
        if len(matches) != 1 or matches[0].get("digest") != MODEL_DIGEST:
            raise ValueError("Model tag differs from expected manifest; review the artifact")
        listing = get_json(origin + "/v1/models")
        save("model-listing", listing)
        if MODEL not in [x.get("id") for x in listing.get("data", [])]:
            raise ValueError("Expected model absent from compatible API")
        print("Running the eight known synthetic cases twice; failures remain in the report", flush=True)
        report = run(origin + "/v1", MODEL, folder/"evaluation", repeats=2, provider="ollama", timeout=180)
        record["model_counts"] = report["counts"]
        save("loaded-model", get_json(origin + "/api/ps"))
        (folder/"resource-snapshot.jsonl").write_text(docker("stats", "--no-stream", "--format", "{{json .}}", server_id)+"\n", encoding="utf-8")
        control = load_fixture("model_cases.json")[0]
        docker("stop", server_id)
        failure = evaluate_case(origin+"/v1", MODEL, control, 1, "ollama", 5)
        save("stopped-provider", failure)
        if failure.get("status") != "error" or failure.get("error_type") not in {"URLError","ConnectionError","ConnectionRefusedError","RemoteDisconnected"}:
            raise ValueError("Stopped provider did not produce the expected transport error")
        docker("start", server_id)
        save("runtime-version-after", wait_ready(origin))
        recovered = evaluate_case(origin+"/v1", MODEL, control, 1, "ollama", 180)
        save("recovery-request", recovered)
        after_tags = get_json(origin + "/api/tags")
        save("model-tags-after", after_tags)
        after_matches = [x for x in after_tags.get("models", []) if x.get("name") == MODEL]
        if len(after_matches) != 1 or after_matches[0].get("digest") != MODEL_DIGEST:
            raise ValueError("Model manifest changed across recovery")
        if recovered.get("status") != "parsed":
            raise ValueError("Recovery did not produce a schema-valid response")
        record["status"] = "lifecycle_pass"
        record["note"] = "Lifecycle pass does not require perfect quality, benign-tool or injection behavior; inspect all model counts."
    except BaseException as error:
        record["status"] = "failed"
        record["error_type"] = type(error).__name__
        raise
    finally:
        retain = keep_running and record["status"] == "lifecycle_pass"
        cleanup = []
        if server_id and not retain:
            try:
                docker("rm", "-f", server_id)
                cleanup.append("owned container removed")
            except Exception:
                cleanup.append("container cleanup failed; inspect recorded ID")
        if network_id and not retain:
            try:
                docker("network", "rm", network_id)
                cleanup.append("owned network removed")
            except Exception:
                cleanup.append("network cleanup failed; inspect recorded ID")
        record.update(finished_utc=datetime.now(timezone.utc).isoformat(), services_retained=retain,
                      cleanup=cleanup, model_volume_retained=True)
        save("result", record)
    print(json.dumps({"status":record["status"], "model_counts":record["model_counts"],
                      "services_retained":record["services_retained"], "model_volume":volume}), flush=True)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--port", type=int, default=18136)
    parser.add_argument("--volume", default="security-lab-starter-models")
    parser.add_argument("--keep-running", action="store_true")
    args = parser.parse_args()
    start(args.output, args.port, args.volume, args.keep_running)
