---
name: vm-connectivity
description: Connect to, discover, and manage this workstation's virtual machines through the vmssh/vmfind helpers and the shared VM credential registry. Use when an agent needs to SSH into a VM, resolve a VM by name or tag, run remote commands, get root on a VM, transfer files, or diagnose failing services on VMs.
---
Skill version: 1.0.0

# VM connectivity
Every VM declared in one file, reached via two POSIX sh helpers on PATH. Mechanism only, never machine specifics.

Registry: `~/.config/vms/registry.env` (gitignored, outside Nix store), four fields per VM: `VM_<IP_UNDERSCORES>_USER` (empty = root), `_PASSWORD`, `_NAME` (short alias), `_TAGS` (space-separated). Dots become underscores (10.0.0.1 → `VM_10_0_0_1_USER`). `$VM_REGISTRY` overrides path (tests use synthetic registry). New VM = four env lines; all agents pick it up.

Discovery: run bare `vmfind` first to inspect configured VMs, users, names, and tags before attempting connection. Never guess hostnames or IPs.

Find: `vmfind [word]` table (IP, user, name, tags); no word = all. Order: literal IP → exact NAME (beats tags) → TAGS substring. Ambiguity lists candidates, never guesses; miss = `no VMs match '<word>'`, non-zero.

Connect: `vmssh <ip|name|tag-words> [command...]` same resolution. Bare = interactive shell; args = one-off (`vmssh mybox 'systemctl status nginx'`). Ambiguous = list + non-zero. Missing password names exact var (`set $VM_10_0_0_1_PASSWORD in ~/.config/vms/registry.env`). Transparently uses workstation SSH key if authorized or falls back to registry password via sshpass. Exit mirrors sshpass/ssh, `&&`/`||` safe. Plain POSIX sh, works non-interactive with no init wrapper.

Root: if target user has passwordless sudo (`sudo -n true`), bare `vmssh mybox 'sudo -n <cmd>'` works directly. Otherwise, load silently (`set -a; . ~/.config/vms/registry.env; set +a`) and pipe to sudo (stdin, never argv/screen): `printf '%s\n' "$VM_10_0_0_1_PASSWORD" | vmssh mybox 'sudo -S <cmd>'`. Never echo password. Assumes sudo = SSH password; on reject, report, do not guess.

Guardrail: service restarts, package install/remove, `rm`, data wipes need explicit user confirmation first. State command + why, wait for go.

Transfer: load as above, password via `SSHPASS` only: `SSHPASS=$VM_10_0_0_1_PASSWORD sshpass -e scp -o StrictHostKeyChecking=no ./file <user>@<ip>:/path`; rsync via `-e 'ssh -o StrictHostKeyChecking=no'`. VM-to-VM relays through workstation.

Diagnosis: long-uptime failures often dead companion unit, not config. `vmssh mybox 'systemctl status <unit>'` (+ deps/runtime) first; fix via sudo idiom, re-verify (`status`/`is-active`).

Escape hatch: raw sshpass/ssh with `SSHPASS` only (tunnels, odd flags): `SSHPASS=... sshpass -e ssh -o StrictHostKeyChecking=no -L 8080:localhost:80 <user>@<ip>`.
