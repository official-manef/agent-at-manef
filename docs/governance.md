# Upstream ownership, forks and release authority

[README](../README.md) · [Contributing](../CONTRIBUTING.md) · [Portability](portability.md)

## Designated roles

The designated public upstream is **rahmanef63/agent-at-manef**, created by Rahman and maintained
with Manef. Repository ownership, product maintenance and commit authorship are separate.
An ownership change does not rewrite previous contributors or change the MIT license.

Use upstream for official documentation, issues, release artifacts, badges and distribution
metadata. A contribution fork is not a second active upstream. Do not advertise duplicated
product homes or treat stars on separate repositories as a combined metric.

A GitHub organization is not required by this toolkit. A future governance decision can choose
an organization as the one upstream, but this runbook does not create it or migrate unrelated
repositories. Client and employer repositories follow their actual ownership agreements.

## Transfer the existing repository, not a replacement

When correcting ownership, use GitHub's transfer mechanism and preserve the original repository
ID, history, issues, PRs, releases and stars. For this project's initial transfer, the repository
ID is `1414110928`. An accepted API request is not proof that a personal-account transfer is done.
The recipient must complete GitHub's acceptance step where required.

Before transferring: verify administrator authority on the source, destination vacancy, repository
visibility, branch/release heads and required integrations. Do not print secret values. Check
repository-attached workflows, hooks and account boundaries after transfer. Preserve current work.

After acceptance: read the destination repository and require the same numeric ID; confirm default
branch and tested source revision; verify the maintainer's collaborator access; then update remotes,
README/badges/package URLs and contributor instructions. Review CI at the new address.

This document specifies the desired arrangement. Its presence alone does not prove that a
transfer, collaborator grant, fork, or synchronization occurred.

## Do not reuse the old address too early

GitHub normally redirects the old address after a transfer. Creating a repository or fork at
that address removes the redirect. First update official URLs and verify ownership. Only then
reuse `official-manef/agent-at-manef` as a contribution fork of the new upstream, if the address is
available. Do not create a copy under the destination to bypass pending acceptance.

When a fork is created, verify its `fork` flag and `parent`/`source` metadata point to the
intended upstream ID, rather than assuming the name establishes ancestry. No private context
workspace belongs in this public fork network.

## Safe fork workflow

```text
rahmanef63/agent-at-manef:main          official source and release authority
             |
             | explicit upstream sync, no force
             v
official-manef/agent-at-manef:main      tracking branch only
             |
             +-- work/topic       reviewed change -> upstream PR
```

Before sync, inspect ahead/behind state and any feature branches. Keep unique work on its own
branch; stop when ancestry or ownership is uncertain. For a verified fork, GitHub offers:

```sh
gh repo sync official-manef/agent-at-manef --branch main
```

This example assumes the transfer and real fork have already been verified. Do not use `--force`.
A conflict needs reconciliation and review, not a reset. Re-read both branch heads after syncing.
The command is not an automatic recurring job, and this repository installs no sync schedule.

For local contributions, use a fork as `origin`, canonical upstream as `upstream`, and create
feature branches from the reviewed upstream revision. Use pull requests for contribution, and
keep consumer deployments pinned to a tested release/revision rather than auto-following main.
Fork only projects an account actually contributes to; a clone or package install suffices for
ordinary consumption.

## Evidence and references

Record the repository IDs, exact revisions, collaborator checks, fork ancestry, ahead/behind
state and CI results in the relevant project tracker. Do not expose private integration metadata
in public issue comments. Recheck current GitHub requirements at execution time.

Primary references: [Repository transfer](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository) ·
[Fork synchronization](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork).

## Branding update — 11 October 2026

The same repository ID 1414110928 was renamed to agent-at-manef. Product display name is
Agent@Manef. The desired owner remains rahmanef63; official-manef maintains the product.
A rename is not transfer acceptance. Re-read the stable repository ID to resolve the current
owner/name, verify pending transfer state, and do not restart or cancel a transfer speculatively.
Update an acceptance-dependent URL only after the destination exists. Future organization
creation remains deferred. Existing licenses and historical commit authors remain unchanged.


## Routing check — 17 October 2026

The GitHub source read still resolves repository ID `1414110928` under
`official-manef/agent-at-manef`. The designated `rahmanef63/agent-at-manef`
destination returned 404 through the same connection; that does not establish
acceptance. Keep the CI badge and review handoff on the reachable current source
until the same stable ID is verified at the destination. Do not restart, cancel,
or replace the pending transfer. No repository ownership changed in this review.
