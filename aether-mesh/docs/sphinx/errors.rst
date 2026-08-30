Error catalog
=============

The CLI, HTTP API, and this reference share one meaning per code.

========================  ====  ====  ========================================================
Code                      Exit  HTTP  Meaning
========================  ====  ====  ========================================================
``IDENTITY_COLLISION``    35    409   Duplicate cluster-id. Identities unsafe.
``POLICY_SHADOW_FAILED``  36    409   Shadow dataplane saw unexpected denies.
``POLICY_NOT_QUALIFIED``  37    409   Promote without a passing shadow report.
``CLUSTERMESH_KVSTORE``   38    503   Control plane not ready.
``NOT_FOUND``             2     404   Missing object.
``VALIDATION``            2     400   Bad YAML or JSON.
``UNAUTHORIZED``          3     401   Bearer token missing or wrong.
========================  ====  ====  ========================================================
