---
title: Helios hybrid EDA job fabric
sidebar_label: Helios hybrid EDA job fabric
description: Senior guide for a hybrid EDA job fabric. Farm licenses, classified design data, burst pin policy, CLI, DITA, Confluence, and Jira.
pagination_next: null
pagination_prev: null
---

# Helios hybrid EDA job fabric

![Helios hybrid EDA job fabric architecture. Linux CLI, sim-class and pnr-class jobs, farm licenses, on-prem farm and burst compute.](/img/helios-hybrid-eda-job-fabric.jpg)

**Document ID:** HEL-OPS-001  
**Revision:** 1.1  
**Audience:** Design engineers, platform SRE, tool integrators, documentation reviewers  
**Author:** Sujatha R, Senior Technical Writer  
**Source of truth:** Git (DITA maps and topics). Confluence space `HEL` is the published surface.  
**Related product slice:** `helios` CLI and API, revision 1.1  

## Description

This guide explains Helios, the Engineering and Cloud Services (ECS) job fabric for licensed EDA work. You will see how a job is placed on the on-prem farm or on burst compute. You will see how a floating license is checked out. You will see how classified design data stays on the farm. Procedures match the working CLI and API in the `helios` tree. DITA topics, Confluence information architecture, and a Jira documentation workflow sit behind this page. New articles reuse those facts instead of copying them.

## Introduction

Chip design groups run long batch jobs. Circuit simulation and place-and-route need different tool images. Both need a floating license seat on the farm. Design data such as netlists and analog IP is classified. It must not go to burst compute.

Helios is the fabric under those tools. It is not a schematic editor. It is not a vendor GUI. Design engineers submit work with `helios`. The scheduler applies pin policy and quota. The farm license daemon grants `analog_sim` or `place_route`. Artifacts land on the farm volume. Platform engineers operate queues, licenses, and storage. Tool integrators attach CI and new toolchain images.

This document is the human entry point for that system. Command examples were written against Helios 1.1. Task topics in Git stay in draft until a writer pastes a local transcript into the Jira Doc ticket. Concepts, error codes, and policy are already in the structured source.

The documentation set uses the same tools an ECS writing team uses at Analog Devices scale:

- Git and topic-based DITA (concept, task, reference, troubleshooting), with conkeyref reuse for warnings and error codes.
- Confluence space `HEL` for search, labels, and page properties (`topic-id`, persona, rev).
- Jira issue type Doc for intake, SME review, and Definition of Done.
- HTML and CSS for space home layout and callout styling.
- UNIX-style CLI on Linux (the CLI also runs where Python 3.11 is installed).

One fact lives in one place. Shared warnings (classified data must stay on the farm, tokens must not appear in tickets) are reused. `LICENSE_EXHAUSTED`, `QUOTA_EXCEEDED`, `REGION_PIN`, and `NFS_STALE` have one meaning in the CLI, the API, and the troubleshooting topics.

## Prerequisites

### Reader

You know which persona you are. Design engineer means you submit jobs and fetch artifacts. Platform SRE means you operate the farm and use runbooks. Tool integrator means you wire CI or a new image. If you do two roles, follow the stricter data-class rule.

### Access

- A Helios identity that `helios whoami` accepts.
- A project slug. Use `demo` for internal sample data. Use `analog-ip` only when you mean classified analog IP.
- Permission to the farm endpoint. Burst is a placement choice, not a second login.

### Workstation

- Python 3.11 or later, with the `helios` CLI on `PATH` (`pip install -e .` from the `helios` directory).
- A shell. Linux is the farm standard. The slice also runs on Windows if Python is installed.
- Write access to an output directory for artifacts (for example `./helios-out`).

### Input data

- Sample path for the quickstart: `samples/smoke` in the `helios` repo. On a real farm the same tree would appear as `/proj/demo/samples/smoke`.
- For the `demo` project, use only internal sample data. Do not use classified libraries as `--input`. Do not pin `analog-ip` to burst.

### Documentation tools (writers)

- Git branch named `doc/<topic-id>`.
- DITA topic copied from `helios-docs/src/templates/`.
- Jira Doc ticket with persona, topic type, `topic-id`, and a validation method.
- Confluence parent page that already exists in the space tree. Do not create orphan pages.

## Personas and where to read

### Design engineer

Start with the quickstart below. Then use job submit, artifact fetch, CLI reference, and designer troubleshooting. You do not remount NFS. You do not drain licenses.

### Platform SRE

Read architecture and trust boundary first. Run `helios admin status --verbose`. Run `helios admin licenses`. License exhaustion and NFS stale have separate runbooks. Do not mix those pages with designer troubleshooting.

### Tool integrator

Read the trust boundary before you set `--pin burst` in CI. Store tokens in the CI secret store. Fail the pipeline on HTTP 403 / exit 34. Do not paste tokens into Jira or Confluence.

## How Helios places a job

### Job classes and license features

| Job class | Image family | Farm feature |
| --- | --- | --- |
| `sim` | `sim-class` | `analog_sim` |
| `pnr` | `pnr-class` | `place_route` |

A simulation job does not consume a place-and-route seat. Burst compute cannot mint farm features. If `analog_sim` is fully checked out, the job waits or the CLI exits 32. That wait is a license event, not a cloud quota event.

### Farm versus burst

`--pin farm` keeps the job on the on-prem farm. Classified projects must use farm. `--pin burst` is allowed only when the project data class is `internal`. Helios rejects classified data on burst with `REGION_PIN` (CLI exit 34, HTTP 403). Do not change data class to force burst.

### Quota and queue

Each project has a concurrent job quota. Over quota returns `QUOTA_EXCEEDED` (exit 33, HTTP 429). A job in `queued` with reason `LICENSE_EXHAUSTED` is waiting for a farm seat. Do not submit duplicate jobs to jump the line.

### Artifact storage

Succeeded jobs write artifacts on the farm volume. Fetch with `helios job artifacts`. Exit 41 (`NFS_STALE`) means a stale volume handle. Retry once. If it fails again, stop. Page storage on-call with the job id only.

## Quickstart: first successful job

This path uses project `demo` (internal sample data) and farm pin.

1. Confirm identity.

```text
helios whoami
```

You should see your user, default project, endpoint `farm`, and rev `1.1`.

2. Submit a sim-class job.

```text
helios job submit --project demo --class sim --image sim-class:1.1 --pin farm --input samples/smoke
```

Stdout is JSON. Copy `job_id`. `state` should be `succeeded` when seats are free. `placement` should be `farm`. `feature` should be `analog_sim`.

3. Wait until the job is terminal.

```text
helios job wait JOB_ID
```

4. Fetch artifacts.

```text
helios job artifacts JOB_ID --out ./helios-out
```

`./helios-out/smoke.log` should exist. The log lists placement, feature, and image.

If submit fails with exit 32 or the job stays queued, do not retry in a loop. See the failure catalog.

## Submit and fetch (design engineer)

### Submit a job

Prerequisites: project slug, class (`sim` or `pnr`), allow-listed image, pin, input path on a volume you may use.

```text
helios job submit --project PROJECT --class CLASS --image IMAGE --pin PIN --input INPUT_PATH
```

Classified analog IP (project `analog-ip`) must use `--pin farm`. `--pin burst` on that project exits 34.

Optional: `--fail-if-queued` exits 32 if the job cannot start because the feature pool is empty. Use this in CI when queued is a failed build.

### Get job status

```text
helios job get JOB_ID
```

Read `state` and `reason` before you resubmit.

### Get artifacts

```text
helios job artifacts JOB_ID --out OUT_DIR
```

Use this only after a terminal success. Empty manifests or exit 41 belong in troubleshooting, not in a second submit.

## Operate Helios (platform SRE)

### Daily health

```text
helios admin status --verbose
helios admin licenses
```

Check scheduler status, queue depth, and feature `in_use` versus `total`. Probe artifact storage from a farm bastion. Do not probe it from a burst node.

### Injected faults (slice only)

The local slice can drain seats and mark a job for stale fetch so writers can validate runbooks:

```text
helios admin drain-licenses --feature analog_sim
helios admin inject-nfs-stale JOB_ID
```

Do not use inject commands on a production farm. They exist to prove documentation against real exit codes.

## CI integration (tool integrator)

1. Put the Helios token in the CI secret store. Do not echo it. Do not paste it into tickets.
2. Submit with `--pin farm`. Use burst only when the pipeline is approved for burst and the project is `internal`.
3. Treat HTTP 403 / exit 34 as a failed pipeline. Do not retry to “get around” pin policy.
4. On HTTP 429, honor `Retry-After`. Do not stampede the license daemon.
5. Copy artifacts only onto storage that matches data class.

API shape (local slice: `python -m helios.api`):

| Path | Method | Role |
| --- | --- | --- |
| `/v1/jobs` | POST | Submit (`class`, `image`, `pin`, `input`, `project`) |
| `/v1/jobs/{id}` | GET | Status and placement |
| `/v1/jobs/{id}/artifacts` | GET | Manifest and fetch |

Error body uses a `code` field. Branch on `code`, not on message text.

## Failure catalog

| Code | CLI exit | HTTP | What it means | What you do |
| --- | --- | --- | --- | --- |
| `LICENSE_EXHAUSTED` | 32 | 429 | No farm seat for `analog_sim` or `place_route` | Wait or page ECS with feature name and job ids. Burst will not create a seat. |
| `QUOTA_EXCEEDED` | 33 | 429 | Project or user concurrency cap | Ask the project owner. Not a SEV by itself. |
| `REGION_PIN` | 34 | 403 | Pin or data class forbids this placement | Fix pin or pipeline. Do not reclassify to cheat. |
| `NFS_STALE` | 41 | 503 | Artifact volume handle is stale | Retry once after 30 seconds. Then storage on-call. |

Canonical wording lives in `helios-docs/src/reuse/error-codes.dita`. CLI, API, and troubleshooting topics pull the same notes.

## Documentation system (how this set is built)

### Information architecture

Confluence space key `HEL`. The home page is a hub. It does not dump architecture. Parents are persona trees: Start here, Design engineer, Platform / SRE, Tool integrator, Knowledge base, Release notes, Docs governance (restricted).

One DITA topic is one Confluence page. The page property `topic-id` matches the DITA `id` (for example `t_submit_job`). Labels include `helios`, persona, type, and component.

The same topic can appear in two trees. `t_submit_job` and `c_trust_boundary` are one file each, referenced from two maps. Writers do not copy XML.

### Content model

| Prefix | Type | Rule |
| --- | --- | --- |
| `c_` | Concept | What and why. No numbered steps. |
| `t_` | Task | One persona, one goal, numbered steps, stated result. |
| `r_` | Reference | Flags, paths, codes. No tutorial narrative. |
| `ts_` | Troubleshooting | Starts from a symptom the reader already has. Designer pages and SRE runbooks stay separate. |

Release notes are a deliverable from Jira `fixVersion`, not a fifth topic type.

### Reuse

`src/reuse/warnings.dita` holds IP-on-farm and token rules. `src/reuse/error-codes.dita` holds error notes. Topics include them with conkeyref. Change a warning once. Submit, CI, architecture, and CLI stay aligned.

### Review path

Jira states: Intake, Writing, SME review, Editorial, Published, Maintain. Definition of Done includes: correct type, conkeyrefs, Linux or slice transcript for tasks, labels and page properties, a path from space home (no orphans).

Writers copy `helios-docs/src/templates/` and follow `helios-docs/CONTRIBUTING.md`.

### Space styling

`helios-docs/confluence/custom.css` defines callout and code styles for the Confluence space. Keep selectors small so they do not fight a company theme.

## Future scope

- Publish DITA maps through DITA-OT into Confluence (or HTML) from CI, keyed by `topic-id`, so paste-from-XML stops.
- Record a 4 to 6 minute walkthrough of the quickstart and attach it to Start here. Keep a storyboard in Git next to the infographic brief.
- Draw the trust-boundary diagram as SVG and pin it on `c_trust_boundary`.
- Generate OpenAPI from the live `/v1/jobs` handlers and diff it against `r_helios_api` in CI.
- Add a stale-page job: Confluence pages whose `rev` is more than two Helios minor versions behind open a Jira Maintain ticket.
- Replace JSON file state with a real queue and a license daemon stub that holds seats for the life of a running job (the slice currently checks out and releases inside one submit when seats exist).
- Add fairness classes as first-class scheduler objects, matching `c_queue_fairness`.
- Restrict Docs governance in Confluence and export this guide as the space PDF for onboarding.
- Validate every task topic on Linux. Attach the transcript to Jira. Then move the topic from draft to published.

## Document history

| Rev | Change |
| --- | --- |
| 1.1 | First published guide. Aligns CLI 1.1, DITA maps, Confluence tree, and Jira DoD. |

## How this set is sourced

This page is the public guide. The matching CLI, DITA maps, Confluence space tree, and writer playbook were built as a companion Helios slice so every procedure has a product to validate against. Git is the source of truth. Confluence is the delivery surface. Jira carries review and Definition of Done.
