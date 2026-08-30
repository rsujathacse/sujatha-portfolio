CLI reference
=============

``aether`` is the UNIX-style control-plane CLI. JSON on stdout. Canonical error objects on stderr.

whoami
------

Identity, endpoint ``clustermesh``, revision, dataplanes.

mesh bootstrap / status
-----------------------

Creates three clusters (``prod-us``, ``prod-eu``, ``prod-ap``) with unique cluster-ids, WireGuard encryption flag, and kube-proxy replacement.

identity list
-------------

Numeric security identities. Cluster-id is part of the hash. Duplicate cluster-ids emit ``IDENTITY_COLLISION``.

policy compile / shadow / promote
---------------------------------

Compile NetworkPolicy YAML. Shadow-qualify against golden Hubble flows. Promote only a qualified bundle.

flow replay
-----------

Evaluate recorded flows on ``enforce`` or ``shadow``. Drop reasons: ``POLICY_DENIED``, ``IDENTITY_COLLISION``.

tetragon apply / replay
-----------------------

Load a TracingPolicy. Replay process, file, and ``tcp_connect`` events. Actions: ``Observe``, ``Sigkill``, ``Deny``.
