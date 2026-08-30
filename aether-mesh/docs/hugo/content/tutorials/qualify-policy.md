---
title: Qualify a ClusterMesh policy on the shadow dataplane
---

# Qualify a ClusterMesh policy on the shadow dataplane

This Hugo topic is the **task** path for platform SRE. The Sphinx tree is the **reference** path. Both are sourced from Git.

## Goal

Promote `checkout-to-payments` only after golden Hubble flows still forward.

## Steps

1. `aether mesh bootstrap`
2. `aether policy shadow --file samples/policies/checkout-to-payments.yaml --flows samples/flows/golden.jsonl`
3. Confirm `"qualified": true`
4. `aether policy promote --name checkout-to-payments`
5. `aether flow replay --file samples/flows/golden.jsonl --dataplane enforce`

## When shadow fails

Exit **36** `POLICY_SHADOW_FAILED` means the candidate would drop an intended `FORWARDED` flow. Do not widen `cluster:` selectors to "fix" it. Restore unique cluster-ids first if `IDENTITY_COLLISION` is present.
