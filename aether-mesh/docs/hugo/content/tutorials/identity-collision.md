---
title: Restore unique cluster-ids after IDENTITY_COLLISION
---

# Restore unique cluster-ids after IDENTITY_COLLISION

Numeric security identities include **cluster-id**. If `prod-ap` reuses `prod-us` id `1`, the AP frontend replica collides with the US frontend. ClusterMesh policy is then unsafe. Shadow qualification refuses to run.

## Goal

Detect exit **35** and restore unique cluster-ids before promoting NetworkPolicy.

## Steps

1. `aether mesh status` — confirm `unique_cluster_ids` and `identity_collisions`.
2. If you are on the documentation slice only: you may have run `aether admin inject-identity-collision`. Do not run that against a real Cilium mesh.
3. Restore `prod-ap` cluster-id to `3` (re-bootstrap the slice, or set unique ids in production Cilium ClusterMesh).
4. Re-run `aether policy shadow` on golden Hubble flows.
5. Promote only when `"qualified": true`.

## Result

`IDENTITY_COLLISION` is gone. US frontend and AP frontend have different numeric identities. The AP replica stays default-deny to checkout.
