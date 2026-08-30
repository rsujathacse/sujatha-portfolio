# Aether Mesh

Self-qualifying multi-cluster zero-trust control plane. This is a **runnable analog** of Cilium ClusterMesh identity, Hubble flow replay, L3/L7 NetworkPolicy, and Tetragon runtime enforcement — including a **shadow dataplane** that qualifies policy before enforce. It is not Cisco Hypershield and not a fork of Cilium. Architecture matches the senior Isovalent / Hypershield documentation story.

```bash
cd aether-mesh
pip install -e ".[dev]"
aether mesh bootstrap
aether whoami
aether mesh status
aether identity list
aether policy shadow --file samples/policies/frontend-to-checkout.yaml --flows samples/flows/golden.jsonl
aether policy promote --name frontend-to-checkout
python -m aether.api
python -m pytest -q
```

State lives in `AETHER_HOME` (default `./.aether`).

| Command | Role |
| --- | --- |
| `aether whoami` | Identity, mesh endpoint, dataplanes, rev |
| `aether mesh bootstrap` / `status` | Three-cluster mesh, kvstore, encryption |
| `aether identity list` | Numeric security identities (ClusterMesh) |
| `aether policy compile` | Expand NetworkPolicy YAML to a rule table |
| `aether policy shadow` | Self-qualify against golden Hubble flows |
| `aether policy promote` | Move a qualified bundle to the enforce dataplane |
| `aether flow replay` | Hubble-style verdicts and drop reasons |
| `aether tetragon apply` / `replay` | TracingPolicy + Sigkill/Deny |
| `aether admin inject-identity-collision` | Duplicate cluster-id (exit 35) |

Exit codes: `IDENTITY_COLLISION` 35, `POLICY_SHADOW_FAILED` 36, `POLICY_NOT_QUALIFIED` 37, `CLUSTERMESH_KVSTORE` 38.

Docs:

- Operator tutorial (Hugo/Markdown): `docs/hugo/` then `hugo --minify -d public`
- CRD/CLI/error reference (Sphinx + Read the Docs theme): `docs/sphinx/`
- Read the Docs config (repo root): `.readthedocs.yaml`
- Portfolio article: `docs/docs/aether-mesh-self-qualifying-zero-trust.md` in the site root
- Chrome page captures: `python3 scripts/capture_docs_sites.py`
- kind + Cilium lab transcripts: `kind/transcripts/` (real kubectl; Hubble not faked)

