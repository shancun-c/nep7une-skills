# Vault Configuration

This reusable skill ships no active vault path, Git remote, or publication permission.
Resolve configuration with the user before using it; never guess from an author's
machine, a wildcard path, another vault, or a previous installation.

## Required local configuration

Keep machine-specific configuration outside the installed skill and outside any
published file set. Record the exact absolute vault path and verify it exists.
Do not write credentials into this file or into skill source. Each vault has its
own configuration; installing or updating a skill must not replace that state.

## Optional publication configuration

Publication is disabled by default. Local editing does not authorize publication.
Before an authorized publication, establish all of the following:

- The exact destination repository URL and branch approved by the user.
- The independent checkout path, outside the vault and not overlapping it.
- The explicit allowlist of relative files approved for sharing, and any exclusions.
- The scope of the user's publication permission, including whether it is one-time
  or standing permission. Merely finding a configured remote is not permission.

Unknown values remain unset. There is no fallback remote or branch. Confirm the
checkout's fetch and push destinations and current branch against this configuration
before copying anything. Stop on mismatches rather than reconfiguring remotes.

Follow [git-sync-pitfalls.md](git-sync-pitfalls.md) for the only supported publication
policy. Never initialize Git, reset, or perform Git writes inside the live vault.
