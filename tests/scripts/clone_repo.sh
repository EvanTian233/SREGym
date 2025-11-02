#!/usr/bin/env bash
set -euo pipefail

# Config (override via env if you like)
REPO="${REPO:-git@github.com:xlab-uiuc/SREGym.git}"
DEST="${DEST:-sregym}"

# Read key from env: prefer SSH_PRIVATE_KEY, else 'ssh', else SSH_PRIVATE_KEY_B64
if [[ -n "${SSH_PRIVATE_KEY:-}" ]]; then
  KEY_CONTENT="${SSH_PRIVATE_KEY//\\n/$'\n'}"
elif [[ -n "${ssh:-}" ]]; then
  KEY_CONTENT="${ssh//\\n/$'\n'}"
elif [[ -n "${SSH_PRIVATE_KEY_B64:-}" ]]; then
  KEY_CONTENT="$(printf '%s' "$SSH_PRIVATE_KEY_B64" | base64 -d)"
else
  echo "Error: set SSH_PRIVATE_KEY (or 'ssh') or SSH_PRIVATE_KEY_B64 in your environment/.env" >&2
  exit 1
fi

# Install key and seed known_hosts (GitHub) to avoid prompts
mkdir -p ~/.ssh && chmod 700 ~/.ssh
KEY_PATH=~/.ssh/id_ed25519_env
printf '%s\n' "$KEY_CONTENT" > "$KEY_PATH"
chmod 600 "$KEY_PATH"
touch ~/.ssh/known_hosts && chmod 600 ~/.ssh/known_hosts
ssh-keyscan -T 5 -t ed25519,rsa github.com >> ~/.ssh/known_hosts 2>/dev/null || true

SSH_CMD="ssh -i $KEY_PATH -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes"

# If repo doesn't exist: clone (default branch)
if [[ ! -d "$DEST/.git" ]]; then
  echo "Cloning $REPO -> $DEST (default branch)"
  git -c "core.sshCommand=$SSH_CMD" clone --depth 1 "$REPO" "$DEST"
  echo "Repo ready (fresh clone)."
  exit 0
fi

# If remote URL differs: warn & bail (no destructive action)
CURRENT_URL="$(git -C "$DEST" remote get-url origin || echo "")"
if [[ "$CURRENT_URL" != "$REPO" ]]; then
  echo "Existing repo at $DEST has origin=$CURRENT_URL (expected $REPO). Skipping."
  exit 0
fi

# Fetch and fast-forward to origin/HEAD (remote default branch)
git -C "$DEST" -c "core.sshCommand=$SSH_CMD" fetch --prune
# Ensure origin/HEAD is set
git -C "$DEST" remote set-head origin -a >/dev/null 2>&1 || true
DEFAULT_REF="$(git -C "$DEST" symbolic-ref --quiet --short refs/remotes/origin/HEAD || true)" # e.g., origin/main
if [[ -z "$DEFAULT_REF" ]]; then
  echo "Could not determine remote default branch. Skipping update."
  exit 0
fi
DEFAULT_BRANCH="${DEFAULT_REF#origin/}"

# If current branch tracks something, just ff to upstream; else check out default
UPSTREAM="$(git -C "$DEST" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [[ -z "$UPSTREAM" ]]; then
  # Create/switch to default branch tracking origin/default
  git -C "$DEST" checkout -B "$DEFAULT_BRANCH" "$DEFAULT_REF" >/dev/null 2>&1 || \
  git -C "$DEST" checkout "$DEFAULT_BRANCH" >/dev/null 2>&1 || true
fi

# Fast-forward only
if git -C "$DEST" -c "core.sshCommand=$SSH_CMD" merge --ff-only "$DEFAULT_REF" >/dev/null 2>&1; then
  echo "Repo ready (fast-forwarded to $DEFAULT_REF)."
else
  # Fallback to pull --ff-only (covers tracking branches)
  git -C "$DEST" -c "core.sshCommand=$SSH_CMD" pull --ff-only origin "$DEFAULT_BRANCH" || true
  echo "Repo checked; updated if behind."
fi
