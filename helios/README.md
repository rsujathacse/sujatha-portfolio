# Helios hybrid EDA job fabric (slice 1.1)

Local CLI and HTTP API used to validate the Helios operations guide in
`docs/docs/helios-hybrid-eda-job-fabric.md`. Screenshots of these commands live
in `static/img/helios/`.

```bash
cd helios
pip install -e ".[dev]"
helios whoami
helios job submit --project demo --class sim --image sim-class:1.1 --pin farm --input samples/smoke
python -m helios.api
python -m pytest -q
```

State lives in `HELIOS_HOME` (default `./.helios` under the current working directory).

| Command | Role |
| --- | --- |
| `helios whoami` | Identity, default project, endpoint, rev |
| `helios job submit` | Place a sim or pnr job |
| `helios job get` / `wait` | Status |
| `helios job artifacts` | Fetch farm-volume files |
| `helios admin status --verbose` | Scheduler and queue |
| `helios admin licenses` | Farm feature pools |
| `helios admin drain-licenses` | Slice injector |
| `helios admin inject-nfs-stale` | Slice injector |

Exit codes: `LICENSE_EXHAUSTED` 32, `QUOTA_EXCEEDED` 33, `REGION_PIN` 34, `NFS_STALE` 41.
