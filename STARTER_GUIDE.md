# Run the optional CPU model experiment

This path adds a real local model after the model-free baseline and owned-service drills work. It uses only the book's synthetic cases. The model is not an authorization service: the Python evaluator checks proposals separately. Check the code-edition tag and commit against the book before running; book publication and code availability are separate.

## Before starting

Use the companion root and the Python interpreter you selected for the baseline. No pip package or cloud API key is needed. You also need Docker with a running **Linux-container** engine, internet access for the runtime/model downloads, and room for those downloads in Docker's storage. A named volume stores the model separately from the source folder.

On Windows, follow [Docker's installation instructions](https://docs.docker.com/desktop/setup/install/windows-install/), including the current Windows, WSL and virtualization requirements. Start Docker Desktop after installation and wait for its engine to be ready. Installing the application does not by itself start the engine. Do not switch an existing shared engine or reset Docker to make this exercise run: review its other workloads first.

Run these checks in PowerShell:

```powershell
python --version
docker version
docker info --format '{{.OSType}}'
```

The last command must report `linux`; `docker version` must include a Server section. A client version alone is not a running engine. If the command is missing, reopen the shell after installation and check Docker's documented installation path. If it cannot contact the server, start Docker Desktop and resolve its reported problem before proceeding.

The starter limits its container to eight CPU equivalents and 6 GiB RAM, requests no GPU device, and uses a 4,096-token context setting. These are this experiment's settings, **not a verified minimum computer specification**. The host operating system, Docker engine and other programs need memory too. The model download is approximately 2.5 GB; the runtime image and Docker storage need additional disk space. A machine with 6 GiB total RAM is not established as sufficient. Check the measured environment in VERSION_MATRIX.md when comparing your results.

## What will be created

Read `security_lab/starter.py` before running it. It names the pinned Ollama image and expected Qwen model manifest digest. A mutable model tag must still resolve to that digest or the experiment stops. The starter creates:

- Container `security-lab-starter-model`, with no host-directory or Docker-socket mount.
- Dedicated bridge network `security-lab-starter-network`.
- Named model volume `security-lab-starter-models` by default; this survives cleanup to avoid another download.
- A new report directory selected by `--output`.

The published address is `127.0.0.1:18136`, not all host interfaces. The dedicated network can access the internet for the download; it is **not an egress firewall**. Local programs and sufficiently privileged Docker users are still inside the relevant trust boundary. Ollama's local API does not acquire authentication merely because a client supplies an API-key-shaped string. The lab sets `OLLAMA_NO_CLOUD=1`, selects a local model and supplies no cloud credential.

Existing containers/networks with the starter's names cause a refusal. An occupied port causes Docker startup to fail. Inspect the owner rather than stopping an unrelated service; choose another unused port with `--port 18137` if needed. A fresh `--volume security-lab-starter-models-002` lets you test a new download instead of reusing an existing model cache.

## Run the complete lifecycle

```powershell
python -m security_lab.starter `
  --output reports/starter-001
```

Use a new output directory for every run. The command pulls the runtime by digest, starts its owned container, downloads/checks the model, checks the API listing, and sends eight known cases twice. It retains each completed observation as it arrives. Requests are sequential; slower CPUs and downloads take longer. A 180-second socket timeout bounds an individual waiting operation, not total run duration or a server-side inference deadline.

The command then stops its own container, confirms that a request fails because the provider is unavailable, starts the same container again, rechecks its model manifest and sends the first quality case once more. The recovery request is a separate observation; it is not a seventeenth attempt added to the sixteen-attempt model score. Finally, the command removes only its created container and network, retaining the model volume and report files.

`lifecycle_pass` means startup, evaluation/report creation, stopped-provider failure and a schema-valid recovery response completed. It does **not** mean every answer, citation or model proposal was correct. Read the quality and control counts even when the lifecycle succeeds. An evaluator error is not a model refusal and does not count as a passing quality answer.

## Inspect the evidence

Start with `result.json`, then `evaluation/model-report.html` and the corresponding JSON. The report has separate denominators for six quality attempts, two legitimate tool controls and eight injection attempts. Inspect failures by case ID and repeat. The familiar repository cases are regression cases; their original `holdout` labels do not make them unseen now.

Runtime image identity, server version, API model listing, model manifests before/after restart, loaded-model metadata and a resource snapshot are separate files. They describe the observed provider and configuration. A post-run memory snapshot is not peak RAM, and a provider's digest is not independent attestation of every loaded weight byte.

The stopped-provider and recovery files let you distinguish a transport failure from a malformed model response. Never replace a failed record with an old passing report. If setup fails, `result.json` records the failure class and cleanup outcome; the terminal may show a higher-level error. Review the failing phase before rerunning with a new output name.

## Keep the server only when needed

For an additional evaluation against the same model, request retention explicitly:

```powershell
python -m security_lab.starter `
  --output reports/starter-002 --keep-running
```

Retention happens only after lifecycle success. Confirm `services_retained: true` in that run's result before relying on the endpoint. Then run:

```powershell
python -m security_lab.model_eval `
  --endpoint http://127.0.0.1:18136/v1 `
  --model qwen3:4b-instruct-2507-q4_K_M `
  --provider ollama --timeout 180 --repeats 2 `
  --output reports/model-extra-001
```

The Ollama adapter omits the vLLM-specific template field. Both adapters use the same task prompt and synthetic cases. Neither silently repairs JSON or forces output through a JSON grammar. This keeps malformed output observable.

When finished, inspect the saved container/network IDs in `result.json` and confirm that they still identify this run's resources. Remove those exact IDs with `docker rm -f <owned-container-id>` and `docker network rm <owned-network-id>`; replace the angle-bracket placeholders, do not paste them literally. Removing the container stops its model process. Do not run a broad Docker prune. Keep the model volume for later runs; removing that exact volume is an optional deliberate cache deletion after all users of it have stopped.

If the Python process is forcibly killed or the computer restarts, normal cleanup may not execute. The starter records each ownership ID after acquisition, before starting the next acquisition. Saved IDs are the recovery reference when available. A kill or power loss can occur before a write or leave an unreadable report; the file is not a crash-durable journal. If the record is absent or incomplete, inspect the named resources, creation details and configuration to establish ownership before removing anything. A matching name alone does not authorize cleanup. Controlled tests of a container-create failure followed by a cleanup failure used a real disposable network and confirmed its ID remains in the result; those injected failures are not a claim to have tested every process-kill or power-loss timing. A model manifest mismatch should lead to a new reviewed version, not deletion of the expected digest check. A later runtime security update also needs new execution evidence; a pinned image is a reproduction reference, not a promise that it remains appropriate forever.

Official references: [Ollama Docker](https://docs.ollama.com/docker), [local API compatibility](https://docs.ollama.com/api/openai-compatibility), [selected model](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M).
