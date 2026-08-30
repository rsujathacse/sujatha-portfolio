# kind + Cilium lab (one cluster)

This folder records a **real** Kubernetes control plane that was brought up in the Cloud Agent (you do not need to run it on your laptop).

## What actually ran

| Piece | Result |
| --- | --- |
| Docker (vfs driver; overlay2 unsupported in this nested pod) | Up |
| kind v0.27.0, node `kindest/node:v1.32.2` | Up after switching containerd to the **native** snapshotter |
| `kubectl` context `kind-aether` | **Real** `kubectl get nodes` / `get pods` |
| `cilium install --version 1.16.6` | CRDs + operator + envoy attempted |
| Cilium agent datapath | **CrashLoopBackOff** — host has no `vxlan` module; `ipset` / `ip_tables` unavailable in the nested kernel |
| Hubble | **Not started** — Hubble needs a healthy agent (`hubble observe` was not faked) |

Transcripts: `kind/transcripts/`. Screenshots: `static/img/aether-mesh/kind-*.png`.

## Reproduce on a machine that can load kernel modules

Requires Linux with overlay, VXLAN, and iptables (a normal laptop or cloud VM, not this nested Cloud Agent pod):

```bash
kind create cluster --config kind/kind-aether.yaml
cilium install --version 1.16.6 --set operator.replicas=1
cilium status --wait
cilium hubble enable
hubble observe --pod kube-system/coredns
```

Until that datapath is healthy, Aether Mesh (`aether policy shadow`) remains the **documented, testable** policy/Hubble analog.
