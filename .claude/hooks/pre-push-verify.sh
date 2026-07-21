#!/usr/bin/env bash
# PreToolUse hook: run just verify before any git push.
# Claude Code passes tool input as JSON on stdin.

input=$(cat)

# Extract the command value from JSON without depending on python3/jq.
# Input format: {"tool_name":"Bash","tool_input":{"command":"..."}}
if ! echo "$input" | grep -qE '"command"[[:space:]]*:[[:space:]]*"[^"]*git push'; then
  exit 0
fi

echo "🔎 running just verify before push..." >&2
if ! nix develop --command just verify; then
  echo "" >&2
  echo "❌ just verify failed — push blocked. Fix the issues above and retry." >&2
  exit 2
fi
echo "✓ verify passed" >&2
