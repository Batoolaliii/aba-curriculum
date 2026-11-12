#!/usr/bin/env bash
set -euo pipefail

# The cdk-nag rule pack runs as part of synth.
# Inert until you uncomment the plugin in app.py.
echo "== cdk-nag =="
uv run cdk synth --quiet -c hrEmail=batolsulail3@gmail.com

echo "== dependency scan =="
uv run pip-audit || echo "WARNING: pip-audit reported vulnerabilities, triage them"
(cd ui && npm audit --audit-level=high) || echo "WARNING: npm audit reported vulnerabilities, triage them"
