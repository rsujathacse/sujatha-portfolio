NetworkPolicy and TracingPolicy
================================

NetworkPolicy
-------------

``kind: NetworkPolicy``. ``endpointSelector.matchLabels`` selects the subject. Ingress ``fromEndpoints`` may pin ``cluster`` so a same-label replica in another cluster is not trusted. L7 HTTP rules are regex on path plus method.

Default deny
------------

The mesh is default-deny. A flow is ``FORWARDED`` only when at least one **enforce** policy allows it.

Shadow qualification
--------------------

The shadow dataplane compiles a candidate bundle, evaluates it next to live golden flows, and rejects the bundle when an intended ``FORWARDED`` flow would drop (``POLICY_SHADOW_FAILED``, exit 36). Promote is refused without a passing report (``POLICY_NOT_QUALIFIED``, exit 37).

TracingPolicy
-------------

``kind: TracingPolicy``. Selectors: binaries, pod labels, syscall name. Hypershield-style compensating control: kill a shell in a PCI pod while the legitimate ``webapp`` binary continues.
