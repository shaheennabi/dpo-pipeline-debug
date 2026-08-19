#!/usr/bin/env bash
set -euo pipefail

# Locate repository root by checking common candidate paths for data/raw_preferences.jsonl
CANDIDATES=("$(pwd)" "/workspace" "/src" "/work" "/app" "/workdir" "/home" "/root")
ROOT=""
for c in "${CANDIDATES[@]}"; do
  if [ -f "$c/data/raw_preferences.jsonl" ]; then
    ROOT="$c"
    break
  fi
done

# Fallback to script-relative resolution
if [ -z "$ROOT" ] && [ -n "${BASH_SOURCE[0]:-}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ROOT="$(cd "$SCRIPT_DIR" && cd .. && pwd)"
fi

# Final fallback to current working dir
if [ -z "$ROOT" ]; then
  ROOT="$(pwd)"
fi

cd "$ROOT"

# Oracle fix: replace buggy format.py with a corrected implementation
cat > src/format.py <<'PY'
#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "deduped_preferences.jsonl"
OUT_PATH = ROOT / "data" / "final_preferences.jsonl"
MAX_RESPONSE_LENGTH = 180


def truncate_response(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def format_record(record: dict, max_length: int) -> dict:
    return {
        "id": record["id"],
        "prompt": record["prompt"],
        "chosen": truncate_response(record["chosen"], max_length),
        "rejected": truncate_response(record["rejected"], max_length),
    }


def main():
    rows = []
    with IN_PATH.open("r", encoding="utf-8") as infile:
        for line in infile:
            if not line.strip():
                continue
            record = json.loads(line)
            rows.append(format_record(record, MAX_RESPONSE_LENGTH))

    with OUT_PATH.open("w", encoding="utf-8") as outfile:
        for row in rows:
            outfile.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Formatted {len(rows)} preference records to {OUT_PATH}")


if __name__ == "__main__":
    main()
PY

# Locate repository root by searching for a directory containing both 'src' and 'tests'
REPO_ROOT=""
REPOS_CANDIDATES=("/workspace" "/src" "/work" "/app" "/workdir" "/repo" "/task" "/run" "/mnt" "/home" "/root" ".")
for c in "${REPOS_CANDIDATES[@]}"; do
  if [ -d "$c/src" ] && [ -d "$c/tests" ]; then
    REPO_ROOT="$c"
    break
  fi
done

# fallback: search filesystem (may be slower)
if [ -z "$REPO_ROOT" ]; then
  REPO_ROOT="$(python - <<'PY'
from pathlib import Path
import sys
for root in ['/', '/workspace', '/src', '/app', '/work', '/workdir', '/repo', '/task', '/run', '/mnt', '/home']:
    p = Path(root)
    if not p.exists():
        continue
    for d in p.rglob('tests'):
        cand = d.parent
        if (cand / 'src').exists():
            print(str(cand))
            sys.exit(0)
# last resort: current dir if it looks like a repo
p = Path('.')
if (p / 'src').exists() and (p / 'tests').exists():
    print(str(p.resolve()))
else:
    print('')
PY
)"
fi

if [ -z "$REPO_ROOT" ]; then
  echo "ERROR: could not locate repository root containing src/ and tests/" >&2
  exit 1
fi

# Run pipeline using corrected formatter
python "$REPO_ROOT/src/parse.py"
python "$REPO_ROOT/src/dedup.py"
python "$REPO_ROOT/src/format.py"

COUNT=$(python - <<'PY'
import json
from pathlib import Path
root = Path('data')
path = root / 'final_preferences.jsonl'
with path.open('r', encoding='utf-8') as fh:
    rows = [json.loads(line) for line in fh if line.strip()]
print(len(rows))
PY
)

echo "Oracle: Generated ${COUNT} final preference records."
