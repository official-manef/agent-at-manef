# Assessment contract

[Library](library.md) · [Requirements example](../examples/requirements.json) · [Target example](../examples/target-profile.json)

Assessment compares declarations only. It never probes a runtime, validates source truth,
checks date freshness, connects an account or grants execution authority.

| Object | Required fields | Rules |
|---|---|---|
| Requirements | schema_version, required, optional | Version 1; unique lists of namespaced identifiers; no overlap |
| Target | schema_version, target_id, claims | Version 1; lowercase stable slug; map of capability declarations |
| Claim | status, evidence, observed_at | supported/unsupported/unknown; bounded reference; ISO date or null |

Supported prefixes are model, harness, host, storage, protocol and tool. Capability identifiers
are intentionally not vendor names. The consuming application defines and tests their actual
meaning. Each list/map is bounded to 128 entries; each input object is bounded to 64 KiB.
Unknown fields, duplicate JSON keys, invalid dates and unsafe text are refused.

For a required capability, missing or unknown declarations block compatibility. An explicitly
unsupported capability also blocks it. Supported claims with no evidence reference or date
are classified unsubstantiated and block compatibility. Optional gaps are reported separately.
An empty required set has required_count 0 and is vacuously compatible, not deployment-ready.

```sh
python -m agent_at_manef assess --requirements examples/requirements.json --target-profile examples/target-profile.json
```

The synthetic example intentionally exits 2. Exit 0 means compatible declarations, exit 2
means unmet requirements, and exit 1 means invalid input. The JSON response always keeps
runtime_probed, evidence_verified, evidence_freshness_checked and deployment_authorized false.
References are not fetched or echoed into output. A forged/stale declaration can still satisfy
the structural comparison; do not use this as an authorization or security enforcement gate.

Before a host executes work, it must independently verify actual capabilities, evidence,
account identity, project scope and current user authority. A directory name, provider label
or capability file does not create that permission. Target deployment records stay separate
from canonical agent identity and are not automatically included in context backups.
