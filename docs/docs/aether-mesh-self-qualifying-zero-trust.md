---
title: Aether Mesh self-qualifying zero-trust
sidebar_label: Aether Mesh ClusterMesh analog
description: Senior operator guide for a Cilium ClusterMesh and Tetragon analog with a Hypershield-style shadow dataplane. Hugo, Sphinx, Git, CLI, and API.
pagination_next: null
pagination_prev: null
---

# Aether Mesh: self-qualifying multi-cluster zero-trust

**Document ID:** AETH-OPS-001  
**Revision:** 1.0  
**Audience:** Platform SRE, network security engineers, solution architects, documentation reviewers  
**Author:** Sujatha R, Senior Technical Writer  
**Source of truth:** Git. Hugo/Markdown tutorials in `aether-mesh/docs/hugo`. Sphinx/reST reference in `aether-mesh/docs/sphinx`.  
**Related product slice:** `aether` CLI and API, revision 1.0  

## Description

This guide is the human entry point for Aether Mesh, a **runnable analog** of Cilium ClusterMesh identity, Hubble flow replay, identity-aware L3/L7 NetworkPolicy, and Tetragon runtime enforcement. A **shadow dataplane** qualifies policy against golden Hubble flows before promote — the same dual-dataplane idea as Cisco Hypershield self-qualifying updates, implemented in the open so writers can validate procedures.

## Introduction

A shop-prod mesh spans `prod-us`, `prod-eu`, and `prod-ap`. Checkout in the US talks to payments in the EU. Payments talks to inventory in AP. A frontend replica in AP shares labels with the US frontend but must **not** inherit its identity. Numeric security identities include cluster-id. Duplicate cluster-ids collide. Policy that is only label-based then becomes unsafe.

The mesh is default-deny. Hubble-style JSONL carries intent (`FORWARDED` or `DROPPED`). You compile NetworkPolicy YAML, run it on the shadow dataplane, and promote only when unexpected denies on golden flows are zero. Tetragon TracingPolicy then kills a shell in the PCI payments pod while the legitimate `webapp` binary continues — a compensating control during an exploit window.

Documentation for this slice uses the Isovalent JD toolchain:

- **Git** revision management (`aether-mesh/` in this repository).
- **Markdown** tutorials built with **Hugo** (`aether-mesh/docs/hugo`, `hugo --minify`).
- **reStructuredText** CLI, policy, and error catalog built with **Sphinx** and the **Read the Docs** theme.
- **Read the Docs** project config at repo root: `.readthedocs.yaml`.
- **UNIX CLI** and HTTP API with one meaning per error code.
- **kind + kubectl + Cilium CLI** on one cluster (agent datapath blocked in this nested VM; Hubble not invented).

## kind + Cilium (one cluster) lab

You do not need to run this on a laptop. The Cloud Agent created `kind-aether` (Kubernetes **v1.32.2**). Commands below are the **captured** session.

```text
kind create cluster --config aether-mesh/kind/kind-aether.yaml
kubectl get nodes -o wide
cilium install --version 1.16.6 --set operator.replicas=1
cilium status
kubectl -n kube-system logs -l k8s-app=cilium
```

![Real `kubectl get nodes -o wide` on kind-aether: control-plane Ready, containerd, kernel 6.12.94+.](/img/aether-mesh/kind-kubectl-nodes.png)

![Real `kubectl get pods -A`: etcd/apiserver/scheduler Running; Cilium agent CrashLoopBackOff; CoreDNS Pending on CNI.](/img/aether-mesh/kind-kubectl-pods.png)

![Real `cilium status`: Helm 1.16.6, Hubble Relay disabled, agent not ready.](/img/aether-mesh/kind-cilium-status.png)

![Real cilium-agent fatal: ipset / iptables modules unavailable in this nested kernel (earlier: VXLAN operation not supported).](/img/aether-mesh/kind-cilium-agent-fatal.png)

Hubble observe was **not** run against empty or fabricated flows. On a host with VXLAN and iptables (a normal Linux VM), the same `kind-aether.yaml` plus `cilium hubble enable` is the next step. Until then, golden JSONL replay in `aether flow replay` is the documented Hubble analog.

Raw transcripts: `aether-mesh/kind/transcripts/`.

## Prerequisites

### Reader

Platform SRE operates the mesh and shadow pipeline. Network security owns NetworkPolicy and TracingPolicy. Solution architects read identity and ClusterMesh failure modes. Writers capture local transcripts before they publish a task topic.

### Workstation

- Python 3.11 or later.
- `pip install -e ".[dev]"` from `aether-mesh/`.
- `aether` on `PATH`.
- Optional: `sphinx-build` for the reference HTML.

### Access

- `AETHER_HOME` for slice state (default `./.aether`).
- Bearer token `slice-token` when `AETHER_ALLOW_ANON` is unset.

## Personas

### Platform SRE

Start with bootstrap, `mesh status`, and identity list. You own cluster-id uniqueness and kvstore health. You do not invent L7 paths to “make shadow pass.”

### Network security

Own NetworkPolicy YAML and TracingPolicy. Shadow-qualify every bundle. Treat exit 36 as a failed change, not as a hint to widen `cluster:` selectors.

### Solution architect

Read identity hashing, default deny, and why an AP frontend replica is untrusted. Use the architecture diagram with customers. Do not present this slice as Cisco software.

## Quickstart

```text
cd aether-mesh
pip install -e ".[dev]"
aether mesh bootstrap
aether whoami
aether mesh status
aether identity list
```

![Live `aether whoami`: identity platform-sre, endpoint clustermesh, shadow and enforce dataplanes, rev 1.0.](/img/aether-mesh/01-whoami.png)

![Bootstrap creates shop-prod with six workloads, WireGuard, kube-proxy replacement, unique cluster-ids, kvstore ready.](/img/aether-mesh/02-mesh-bootstrap.png)

![Numeric identities: cluster-id is part of the hash. US frontend and AP frontend differ until cluster-ids collide.](/img/aether-mesh/03-identity-list.png)

## Shadow qualification (self-qualifying updates)

Hypershield tests policy on a dual dataplane before enforcement. Aether Mesh does the same with golden Hubble JSONL.

```text
aether policy shadow --file samples/policies/frontend-to-checkout.yaml --flows samples/flows/golden.jsonl
aether policy promote --name frontend-to-checkout
```

Repeat for `checkout-to-payments.yaml` and `payments-to-inventory.yaml`. Shadow only scores flows the policy subjects (ingress to the selected endpoint). A checkout ingress policy is not failed because payments-to-inventory is still default-deny.

![Shadow report: bundle frontend-to-checkout, qualified true, unexpected_denies empty, SLO max unexpected deny 0.](/img/aether-mesh/04-policy-shadow.png)

![Promote copies a qualified bundle onto the enforce dataplane.](/img/aether-mesh/05-policy-promote.png)

### Overreach is a failed change

A candidate that rewrites `POST /v1/charge` to `/v2/charge-only` drops a golden FORWARDED flow. The CLI exits **36** `POLICY_SHADOW_FAILED`. Do not promote.

![Overreach L7 path: POLICY_SHADOW_FAILED, exit 36.](/img/aether-mesh/07-shadow-failed.png)

Promote without a passing report exits **37** `POLICY_NOT_QUALIFIED`.

## Hubble replay on the enforce dataplane

```text
aether flow replay --file samples/flows/golden.jsonl --dataplane enforce
```

Expected on a fully promoted baseline: **3 forwarded**, **2 dropped**.

| Flow | Verdict | Why |
| --- | --- | --- |
| frontend@us GET /api/cart → checkout | FORWARDED | `frontend-to-checkout` |
| checkout@us POST /v1/charge → payments | FORWARDED | `checkout-to-payments` |
| payments GET /sku → inventory | FORWARDED | `payments-to-inventory` |
| frontend@us GET /v1/charge → payments | DROPPED | Default deny; skips checkout |
| frontend@ap GET /api/cart → checkout | DROPPED | Peer pins `cluster: prod-us` |

![Enforce replay: three FORWARDED east-west paths, two POLICY_DENIED drops including the AP frontend replica.](/img/aether-mesh/06-flow-replay.png)

## Tetragon: exploit window without patching the app

```text
aether tetragon apply --file samples/tetragon/payments-enforcer.yaml
aether tetragon replay --file samples/tetragon/exploit-window.jsonl
```

The legitimate `webapp` binary is observed. `/bin/sh` and `curl` in the payments pod are **Sigkill**. `file_open` from `webapp` is **Deny**. That is the documentation story for distributed exploit protection: surgical kernel-level control while the app stays up.

![Tetragon replay: 5 events, 3 enforced; webapp observed; shell and curl Sigkill.](/img/aether-mesh/09-tetragon-exploit.png)

## Identity collision (ClusterMesh operational failure)

```text
aether admin inject-identity-collision
```

The injector sets `prod-ap` cluster-id to **1**, colliding with `prod-us`. US frontend and AP frontend share a numeric identity. Shadow refuses to qualify. CLI exits **35** `IDENTITY_COLLISION`. Restore unique cluster-ids before you promote anything.

![IDENTITY_COLLISION, exit 35, when two clusters share a cluster-id.](/img/aether-mesh/10-identity-collision.png)

This injector is for documentation and tests. Do not use it against a real Cilium mesh.

## HTTP API

`python3 -m aether.api` (default `127.0.0.1:8787`).

| Path | Method | Role |
| --- | --- | --- |
| `/v1/healthz` | GET | Rev |
| `/v1/mesh` | GET | Health, cluster-ids, collisions |
| `/v1/identities` | GET | Numeric identities |
| `/v1/policies/shadow` | POST | `{policy, flows}` |
| `/v1/policies/{name}/promote` | POST | Enforce after qualification |
| `/v1/flows/replay` | POST | Hubble analog |
| `/v1/tetragon/policies` | POST | TracingPolicy |
| `/v1/tetragon/events` | POST | Runtime replay |

![GET /v1/mesh after bootstrap: healthy shop-prod, six workloads, WireGuard.](/img/aether-mesh/11-api-mesh.png)

## Failure catalog

| Code | CLI exit | HTTP | What it means | What you do |
| --- | --- | --- | --- | --- |
| `IDENTITY_COLLISION` | 35 | 409 | Duplicate cluster-id | Restore unique ids. Do not promote. |
| `POLICY_SHADOW_FAILED` | 36 | 409 | Unexpected deny on golden flows | Fix the candidate. Do not widen trust. |
| `POLICY_NOT_QUALIFIED` | 37 | 409 | Promote without shadow pass | Run shadow first. |
| `CLUSTERMESH_KVSTORE` | 38 | 503 | Control plane not ready | Wait; check kvstore. |
| `UNAUTHORIZED` | 3 | 401 | Bad or missing bearer | Fix the secret, not the policy. |

CLI, API, Sphinx `errors.rst`, and this table share one meaning per code.

## Documentation system

| Surface | Format | How it is built |
| --- | --- | --- |
| Operator tutorial | Hugo + Markdown | `cd aether-mesh/docs/hugo && hugo --minify -d public` |
| CLI / CRD / errors | Sphinx + reST + RTD theme | `sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html` |
| Read the Docs | `.readthedocs.yaml` | Sphinx config `aether-mesh/docs/sphinx/conf.py` |
| This portfolio guide | Docusaurus Markdown | `docs/docs/aether-mesh-self-qualifying-zero-trust.md` |
| Product slice | Python CLI/API | `aether-mesh/aether/` |

```text
# Hugo (task docs)
cd aether-mesh/docs/hugo
hugo version
hugo --minify -d public

# Sphinx / Read the Docs theme (reference)
cd aether-mesh
pip install -r docs/sphinx/requirements.txt
python3 -m sphinx -W -b html docs/sphinx docs/sphinx/_build/html
```

![Live `hugo --minify -d public` on Hugo 0.134.3 extended: 5 pages in 9 ms.](/img/aether-mesh/hugo-build.png)

![Hugo operator home, served from `public/` at `/aether-mesh/`.](/img/aether-mesh/hugo-home.png)

![Hugo task topic: qualify ClusterMesh policy on the shadow dataplane.](/img/aether-mesh/hugo-qualify-policy.png)

![Sphinx HTML with the Read the Docs theme (what `.readthedocs.yaml` builds).](/img/aether-mesh/rtd-sphinx-home.png)

![Error catalog on the RTD theme: one meaning per code for CLI, API, and reference.](/img/aether-mesh/rtd-sphinx-errors.png)

Chrome captured those HTML pages from local HTTP servers after the Hugo and Sphinx builds. Task topics stay in draft until a writer pastes a local CLI transcript (`scripts/render_docs_screenshots.py`). Page captures: `scripts/capture_docs_sites.py`.

## Future scope

- Generate NetworkPolicy reference from YAML schemas into Sphinx autodoc.
- Export Hubble-compatible protobuf instead of JSONL.
- Vale + GitHub Actions on Hugo and reST in the same PR.
- Card-sort IA study: SRE vs SecOps vs SA nav (task-based vs product-based).
- Optional kind lab that points Hubble export at this qualifier.

## Document history

| Rev | Change |
| --- | --- |
| 1.0 | First published guide. Aligns CLI 1.0, Hugo tutorials, Sphinx reference, and live transcripts in `static/img/aether-mesh/`. |
| 1.2 | kind-aether lab: real kubectl nodes/pods, Cilium 1.16.6 install, agent CrashLoop transcripts. Hubble not faked. |
