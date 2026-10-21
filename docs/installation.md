# Installation

Shared Agents installs to **`~/.shared-agents`** by default (override with `$SHARED_AGENTS_HOME`).

## Recommended: bootstrap (one command)

```bash
curl -fsSL https://raw.githubusercontent.com/netgrade-digital/shared-agents/refs/heads/main/scripts/bootstrap.sh | bash
```

The wizard:

1. Clones or updates Core into your home directory
2. Optionally configures your **private team** Git remote
3. Runs **`sa install`** for detected AI tools
4. Adds the **`sa`** shell command to your login shell (`~/.bashrc`, `~/.zshrc`, or fish `~/.config/fish/config.fish`). When fish is installed as well, that config is updated too.

Then open a new terminal, or source the file that was updated:

```bash
source ~/.bashrc                        # bash
source ~/.zshrc                         # zsh
source ~/.config/fish/config.fish       # fish
sa check
sa team verify    # recommended after team setup
```

### Non-interactive (CI / scripts)

```bash
SA_BOOTSTRAP_NON_INTERACTIVE=1 curl -fsSL https://raw.githubusercontent.com/netgrade-digital/shared-agents/refs/heads/main/scripts/bootstrap.sh | bash
```

## Alternative: clone + install

**Core only** (team repo optional in wizard):

```bash
git clone git@github.com:netgrade-digital/shared-agents.git ~/.shared-agents
cd ~/.shared-agents
sa install
source ~/.bashrc   # fish: source ~/.config/fish/config.fish
```

**From a dev checkout** (repo on disk, install into home):

```bash
git clone git@github.com:netgrade-digital/shared-agents.git ~/Development/shared-agents
cd ~/Development/shared-agents
./sa install --home "$HOME/.shared-agents"
source ~/.bashrc   # fish: source ~/.config/fish/config.fish
```

## Install wizard (`sa install`)

Interactive when run in a TTY:

```bash
sa install
```

| Step | What you choose |
|------|-----------------|
| Install path | Default `~/.shared-agents` or custom |
| Tools | Which adapters to configure (↑↓, Space, `a` all, `d` detected) |
| Team repo URL | Optional private remote for learnings/skills/rules |
| Shell CLI | Add `sa` to bash, zsh, and fish |

Quick / CI:

```bash
sa install --non-interactive
sa install --non-interactive --tools cursor,claude-code
sa install --dry-run
```

Alias: **`sa install`** = **`sa setup`**

## After installation

| Check | Command |
|-------|---------|
| Tools configured | `sa check` |
| Team layout OK | `sa team verify` |
| Open tasks | `sa status` |
| Live command list | `sa help` |

## New AI tool on your machine?

Run **`sa install`** again — it only configures tools detected as installed.

## Development setup (Core contributors)

```bash
git clone git@github.com:netgrade-digital/shared-agents.git
cd shared-agents
./sa install --home "$HOME/.shared-agents"
source ~/.bashrc   # fish: source ~/.config/fish/config.fish
sa install --dry-run
sa check
```

Work in the clone; test with `sa` pointing at `$SHARED_AGENTS_HOME`. See [Contributing](/docs/contributing).

## Uninstall

```bash
sa uninstall              # prompts
sa uninstall -y
sa uninstall --keep-repo  # remove adapters only; keep ~/.shared-agents
```

Then open a new terminal (`source ~/.bashrc`, `source ~/.zshrc`, or `source ~/.config/fish/config.fish`). Fresh setup: **`sa bootstrap`**.

## Troubleshooting

See [Troubleshooting](/docs/troubleshooting) for `sa: command not found`, half-finished wizard, and adapter issues.
