# Getting started

Run commands from a reviewed checkout of this repository in a Bash shell.
Do not install into a vault, your home directory, or a general-purpose folder.
The destination must be a dedicated skill directory.

## Prerequisites and scope

- Git to obtain a checkout; Bash and Python 3 for the installers.
- A host runtime that can discover the installed skills. Confirm its current
  discovery rules; copying files alone does not verify activation.
- The required companion skills below, installed from sources you trust.
  This repository does not download, pin, or certify them.
- Stop the host runtime, editor, and sync client before a real install/update.
  Use a disposable directory first. Native Windows/macOS behavior is unverified.
  Do not treat Git Bash or WSL as equivalent to a native Windows test.

```bash
git clone https://github.com/shancun-c/nep7une-skills.git
cd nep7une-skills
python3 --version
bash --version
```

Clone downloads the source; it does not install skills. Review the source and
[maintenance rules](maintenance.md) before executing it.

## Required companion skills

| Skill | Codex | Hermes | OpenClaw |
| --- | --- | --- | --- |
| `obsidian-wiki-skill` | `obsidian-markdown`, `obsidian-cli`, `obsidian-bases`, `json-canvas` | `obsidian` | `obsidian` |
| `knowledge-canvas-sync` | `obsidian-canvas-creator`, `obsidian-markdown` | `obsidian-canvas-creator`, `obsidian` | `obsidian-canvas-creator` |
| `server-ops-skill` | No required companion skill | No required companion skill | No required companion skill |

The [registry](../registry.yaml) also lists recommended and optional companions.
`json-canvas` is used by Wiki but is **not** a replacement for Canvas Creator in
Knowledge Canvas. Dependency checks identify companion `SKILL.md` files under
the selected skills root; they do not exercise the companion or inspect its
version. The Server Ops workflows need working local SSH and a private SSH
configuration, but the current shell dependency checker does not validate those
tools, credentials, aliases, or connectivity. No server operation is performed
by installing Server Ops.

## Choose the target

| Runtime | Default installed path | Override |
| --- | --- | --- |
| Codex | `${CODEX_HOME:-$HOME/.codex}/skills/nep7une-skills/<skill>` | `--skills-dir ROOT` or `--target FULL_SKILL_DIRECTORY` |
| Hermes | `${HERMES_HOME:-$HOME/.hermes}/skills/nep7une-skills/<skill>` | `--skills-dir ROOT` or `--target FULL_SKILL_DIRECTORY` |
| OpenClaw | No implicit workspace | `--target WORKSPACE` or `--skills-dir ROOT` |

For Codex/Hermes, `--target` is the full skill directory and must end with the
selected skill name. Dependency lookup and backup placement still use the
skills root; when overriding the target, set `--skills-dir` consistently too.
For OpenClaw, `--target` means the **workspace**, so installation goes beneath
`WORKSPACE/skills/nep7une-skills/<skill>`. Do not supply both OpenClaw target flags.

## Preview, then install one skill

All three installers default to Wiki. The following examples select it
explicitly. Required companions must already exist in the chosen skills root.

```bash
bash installers/install-codex.sh --skill obsidian-wiki-skill --dry-run
bash installers/install-codex.sh --skill obsidian-wiki-skill
```

```bash
bash installers/install-hermes.sh --skill obsidian-wiki-skill --dry-run
bash installers/install-hermes.sh --skill obsidian-wiki-skill
```

For OpenClaw, replace the example workspace value with a dedicated path you
intend to use; do not paste an unedited placeholder into a production command.

```bash
WORKSPACE="$HOME/openclaw-workspace"
bash installers/install-openclaw.sh --target "$WORKSPACE" --skill obsidian-wiki-skill --dry-run
bash installers/install-openclaw.sh --target "$WORKSPACE" --skill obsidian-wiki-skill
```

Replace `obsidian-wiki-skill` with `knowledge-canvas-sync` or `server-ops-skill`
to select another skill. Dry run still checks required dependencies and paths;
a failure is not permission to bypass the check. Use `--skip-deps` only for an
intentional packaging experiment, such as the [isolated example](examples.md),
not as a fix for a missing runtime dependency.

## First runtime use

After installation, verify that the runtime discovers the intended skill and
companions. Start with a read-only prompt against an explicitly selected test
vault, for example: “Use obsidian-wiki-skill to orient to this test vault and
report what you find. Do not write files.” Inspect the output before authorizing
writes. The example prompts in the README describe workflows; they do not prove
runtime activation, configure schedules, or authorize SSH/server changes.
