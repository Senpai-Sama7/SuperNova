#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TS="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
PROOF_DIR="proof_bundle/${TS}"

mkdir -p \
  "${PROOF_DIR}/00_meta" \
  "${PROOF_DIR}/01_quality" \
  "${PROOF_DIR}/02_perf" \
  "${PROOF_DIR}/03_cost" \
  "${PROOF_DIR}/04_reliability" \
  "${PROOF_DIR}/05_security" \
  "${PROOF_DIR}/06_dx" \
  "${PROOF_DIR}/07_ux" \
  "${PROOF_DIR}/08_competitive" \
  "${PROOF_DIR}/09_release"

echo "[proof] writing to ${PROOF_DIR}"

STATUS_FILE="${PROOF_DIR}/00_meta/step_status.txt"
touch "${STATUS_FILE}"

run_step() {
  local name="$1"
  shift
  set +e
  "$@"
  local rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    echo "${name}=PASS" >> "${STATUS_FILE}"
  else
    echo "${name}=FAIL(${rc})" >> "${STATUS_FILE}"
  fi
  return 0
}

{
  echo "timestamp_utc=${TS}"
  echo "root=${ROOT_DIR}"
} > "${PROOF_DIR}/00_meta/run_meta.txt"

run_step "meta_commit" git rev-parse HEAD > "${PROOF_DIR}/00_meta/commit.txt"
run_step "meta_status" bash -c "git status --short > '${PROOF_DIR}/00_meta/git_status.txt'"
run_step "meta_diffstat" bash -c "git diff --stat > '${PROOF_DIR}/00_meta/diffstat.txt'"
run_step "meta_system" bash -c "{
  uname -a
  python3 --version
  node --version || true
  docker --version || true
} > '${PROOF_DIR}/00_meta/system.txt' 2>&1"

echo "[proof] quality checks"
run_step "quality_suite" bash -c "(cd supernova && pytest tests/ --cov=supernova --cov-fail-under=80 -q > '../${PROOF_DIR}/01_quality/pytest_full.txt' 2>&1)"
run_step "quality_warning_gate_cost_controller" bash -c "(cd supernova && pytest tests/test_cost_controller.py -q --no-cov -W error::RuntimeWarning > '../${PROOF_DIR}/01_quality/pytest_warning_gate_cost_controller.txt' 2>&1)"
run_step "quality_flake_repeats" bash -c "(cd supernova && for i in 1 2; do pytest tests/ -q --no-cov > '../${PROOF_DIR}/01_quality/flake_run_'\"\$i\"'.txt' 2>&1; done)"

echo "[proof] security checks"
run_step "security_checks" bash -c "(cd supernova && python3 -m pip install -q pip-audit > /dev/null 2>&1 || true; pip-audit > '../${PROOF_DIR}/05_security/pip_audit.txt' 2>&1 || true; ruff check . > '../${PROOF_DIR}/05_security/ruff_check.txt' 2>&1 || true; rg -n '(API_KEY|SECRET|TOKEN|PASSWORD)=' -g '!*.md' . > '../${PROOF_DIR}/05_security/plaintext_secret_scan.txt' 2>&1 || true)"

echo "[proof] dx check"
DX_START="$(date +%s)"
run_step "dx_uv_sync" bash -c "(cd supernova && uv sync > '../${PROOF_DIR}/06_dx/uv_sync.txt' 2>&1 || true)"
DX_END="$(date +%s)"
echo "setup_seconds=$((DX_END - DX_START))" > "${PROOF_DIR}/06_dx/setup_time.txt"

echo "[proof] perf/cost/reliability checks"
UVICORN_LOG="${PROOF_DIR}/04_reliability/uvicorn.log"
run_step "api_start" bash -c "(cd supernova && { nohup uvicorn api.gateway:app --host 127.0.0.1 --port 8000 --log-level warning > '../${UVICORN_LOG}' 2>&1 & echo \$! > '../${PROOF_DIR}/04_reliability/uvicorn.pid'; })"
sleep 5

run_step "reliability_health_initial" bash -c "curl -sS http://127.0.0.1:8000/healthz > '${PROOF_DIR}/04_reliability/health_initial.json'"
if grep -q "reliability_health_initial=PASS" "${STATUS_FILE}"; then
  run_step "perf_healthz_latency" bash -c "for i in \$(seq 1 30); do /usr/bin/time -f '%e' curl -sS http://127.0.0.1:8000/healthz >/dev/null; done > '${PROOF_DIR}/02_perf/healthz_latencies_seconds.txt' 2>&1"
  run_step "cost_admin_snapshot" bash -c "curl -sS http://127.0.0.1:8000/admin/costs > '${PROOF_DIR}/03_cost/admin_costs_snapshot.json'"
  for i in 1 2; do
    run_step "reliability_health_before_${i}" bash -c "curl -sS http://127.0.0.1:8000/healthz > '${PROOF_DIR}/04_reliability/health_before_${i}.json'"
    if [[ -f "${PROOF_DIR}/04_reliability/uvicorn.pid" ]]; then
      kill "$(cat "${PROOF_DIR}/04_reliability/uvicorn.pid")" || true
      sleep 2
    fi
    run_step "api_restart_${i}" bash -c "(cd supernova && { nohup uvicorn api.gateway:app --host 127.0.0.1 --port 8000 --log-level warning > '../${PROOF_DIR}/04_reliability/uvicorn_restart_${i}.log' 2>&1 & echo \$! > '../${PROOF_DIR}/04_reliability/uvicorn.pid'; })"
    sleep 5
    run_step "reliability_health_after_${i}" bash -c "curl -sS http://127.0.0.1:8000/healthz > '${PROOF_DIR}/04_reliability/health_after_${i}.json'"
  done
else
  {
    echo "perf/cost/reliability checks skipped because API did not become reachable at 127.0.0.1:8000"
    echo "see ${UVICORN_LOG}"
  } > "${PROOF_DIR}/04_reliability/skipped.txt"
fi

if [[ -f "${PROOF_DIR}/04_reliability/uvicorn.pid" ]]; then
  kill "$(cat "${PROOF_DIR}/04_reliability/uvicorn.pid")" || true
fi

cat > "${PROOF_DIR}/07_ux/README.txt" <<'EOF'
Manual artifacts required:
- non_technical_flow.mp4
- admin_flow.mp4
EOF

cat > "${PROOF_DIR}/08_competitive/README.txt" <<'EOF'
External competitive run required:
1) Save identical prompts to prompts.jsonl
2) Save SuperNova raw outputs to supernova_outputs.jsonl
3) Save OpenClaw raw outputs to openclaw_outputs.jsonl
4) Save scored result to scorecard.csv
EOF

{
  echo "# Changelog"
  echo "- Proof bundle generated automatically."
} > "${PROOF_DIR}/09_release/changelog.md"

cat > "${PROOF_DIR}/09_release/rollback.md" <<'EOF'
# Rollback
1. git checkout <previous_tag_or_commit>
2. restart services
3. validate /healthz
EOF

run_step "release_bundle_tar" tar -czf "proof_bundle_${TS}.tar.gz" -C proof_bundle "${TS}"
run_step "release_bundle_checksum" sha256sum "proof_bundle_${TS}.tar.gz" > "${PROOF_DIR}/09_release/proof_bundle_sha256.txt"

echo "${PROOF_DIR}" > proof_bundle/latest_bundle_path.txt
echo "[proof] done: ${PROOF_DIR}"
