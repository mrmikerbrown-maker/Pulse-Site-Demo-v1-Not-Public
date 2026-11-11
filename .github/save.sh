#!/usr/bin/env bash
# Shared "save the new data" step for every data job in this repo.
# Usage: bash .github/save.sh "Commit message" file-or-folder [more files...]
# Several jobs save into this one repo, so if another job saved first we pull its change and try again.
set -u
msg="$1"; shift
git config user.name "github-actions[bot]"
git config user.email "41898208+github-actions[bot]@users.noreply.github.com"
for p in "$@"; do git add -- "$p" 2>/dev/null || true; done
if git diff --cached --quiet; then echo "Nothing changed"; exit 0; fi
git commit -q -m "$msg"
for i in 1 2 3 4 5 6; do
  if git push -q; then
    echo "Saved"
    # Pushes made by a job don't start a GitHub Pages build on their own, so ask for one.
    gh api -X POST "repos/${GITHUB_REPOSITORY}/pages/builds" >/dev/null 2>&1 || true
    exit 0
  fi
  echo "Another job saved first; pulling its change and trying again ($i)"
  sleep $((i * 5))
  git pull -q --rebase --autostash origin "${GITHUB_REF_NAME}" || exit 1
done
echo "Could not save after 6 tries"; exit 1
