# SSH Safety

## Connection Rules

- Use an SSH alias such as `nep7une-tokyo`; do not hard-code hostnames, IP addresses, users, passwords, or keys in the skill.
- Check alias resolution with `ssh -G <alias>` before first use.
- Prefer one-shot commands: `ssh <alias> '<command>'`.
- Use interactive SSH only when a task cannot be done safely with one-shot commands.
- If SSH authentication fails, stop and ask the user to fix local SSH config. Do not ask the user to paste credentials into the repository.

## Secret Handling

Never commit or print:

- passwords
- private keys
- token values
- `.env` values
- cookies
- wallet files
- session databases
- service credentials

Avoid reading files such as:

- `.env`
- `id_*`
- `*.pem`
- `*.key`
- `wallet*.json`
- `tokens.json`
- `config.json` when likely to contain credentials
- browser cookies or app session files

If the user explicitly asks to inspect a secret-bearing file, explain the risk and prefer checking whether keys exist instead of printing values.

## Redaction

When logs or config output may include secrets, filter obvious values before showing output:

```bash
sed -E 's/(PASSWORD|PASSWD|TOKEN|SECRET|API_KEY|KEY|AUTHORIZATION|COOKIE)=([^[:space:]]+)/\1=[REDACTED]/Ig'
```

This is a helper, not a guarantee. If output may contain secrets, summarize rather than paste.

## Confirmation Gate

Require explicit confirmation before:

- changing SSH policy
- changing firewall policy
- restarting production services
- editing Nginx, Caddy, Apache, systemd, Docker, or PM2 config
- installing or upgrading packages
- rotating credentials
- deleting files
- rebooting

Before asking for confirmation, state:

- intended command or action
- affected service
- expected downtime or risk
- backup path
- rollback path
- verification command
