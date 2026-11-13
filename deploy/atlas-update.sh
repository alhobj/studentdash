#!/usr/bin/env bash
# Managed test checkout only. Never run this inside a working development checkout.
set -euo pipefail
: "${ARBOR_REPO_URL:?Set ARBOR_REPO_URL to your new ArborSynapse repository URL}"
ARBOR_BRANCH="${ARBOR_BRANCH:-main}"
ARBOR_DEPLOY_DIR="${ARBOR_DEPLOY_DIR:-/mnt/user/appdata/arborsynapse-test}"
mkdir -p "$ARBOR_DEPLOY_DIR"
exec 9>"$ARBOR_DEPLOY_DIR/.deploy.lock"
flock -n 9 || exit 0
ARBOR_SOURCE="$ARBOR_DEPLOY_DIR/source"
if [[ ! -d "$ARBOR_SOURCE/.git" ]]; then
  git clone --no-checkout --single-branch --branch "$ARBOR_BRANCH" "$ARBOR_REPO_URL" "$ARBOR_SOURCE"
fi
if [[ "$(git -C "$ARBOR_SOURCE" remote get-url origin)" != "$ARBOR_REPO_URL" ]]; then
  echo 'This managed checkout belongs to a different repository.' >&2; exit 1
fi
if [[ -n "$(git -C "$ARBOR_SOURCE" status --porcelain)" && -f "$ARBOR_SOURCE/arborsynapse.py" ]]; then
  echo 'Managed source has edits. Move them out before updating.' >&2; exit 1
fi
git -C "$ARBOR_SOURCE" fetch --depth 1 origin "$ARBOR_BRANCH"
ARBOR_SHA="$(git -C "$ARBOR_SOURCE" rev-parse FETCH_HEAD)"
if [[ -f "$ARBOR_DEPLOY_DIR/.deployed-sha" && "$(cat "$ARBOR_DEPLOY_DIR/.deployed-sha")" == "$ARBOR_SHA" ]]; then exit 0; fi
git -C "$ARBOR_SOURCE" checkout --detach "$ARBOR_SHA"
cd "$ARBOR_SOURCE"
# Build first: a failed build leaves the existing running service untouched.
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d --wait
printf '%s\n' "$ARBOR_SHA" > "$ARBOR_DEPLOY_DIR/.deployed-sha"
echo "ArborSynapse test updated to $ARBOR_SHA"
