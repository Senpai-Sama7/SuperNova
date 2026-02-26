#!/usr/bin/env bash
set -euo pipefail

repo="${1:-.}"

if ! command -v rg >/dev/null 2>&1; then
  echo "error: ripgrep (rg) not found on PATH" >&2
  exit 2
fi

echo "Android repo audit: ${repo}"
echo

if [[ ! -d "${repo}" ]]; then
  echo "error: repo path not found: ${repo}" >&2
  exit 2
fi

cd "${repo}"

echo "== Key files"
for f in \
  gradlew \
  settings.gradle settings.gradle.kts \
  build.gradle build.gradle.kts \
  gradle.properties \
  local.properties \
  app/build.gradle app/build.gradle.kts \
; do
  if [[ -f "${f}" ]]; then
    echo "found: ${f}"
  fi
done
echo

echo "== Modules (from settings.gradle*)"
if [[ -f settings.gradle.kts ]]; then
  rg -n --no-heading 'include\\(' settings.gradle.kts || true
elif [[ -f settings.gradle ]]; then
  rg -n --no-heading 'include\\s' settings.gradle || true
else
  echo "no settings.gradle(.kts) found"
fi
echo

echo "== Compose usage hints"
rg -n --no-heading --glob '**/*.kt' 'androidx\\.compose\\.|@Composable' . | head -n 30 || true
echo

echo "== Gradle/AGP/Kotlin hints"
rg -n --no-heading 'com\\.android\\.application|com\\.android\\.library|org\\.jetbrains\\.kotlin\\.android|kotlin\\(\"android\"\\)' \
  **/*.gradle **/*.gradle.kts 2>/dev/null | head -n 40 || true
echo

echo "== SDK config hints (min/target/compile)"
rg -n --no-heading 'minSdk|targetSdk|compileSdk' **/*.gradle **/*.gradle.kts 2>/dev/null | head -n 60 || true
echo

echo "== Testing hints"
rg -n --no-heading 'androidTest|testImplementation|androidx\\.test|junit|espresso' \
  **/*.gradle **/*.gradle.kts **/*.kt 2>/dev/null | head -n 60 || true
echo

echo "== Networking / persistence hints"
rg -n --no-heading 'retrofit|okhttp|ktor|room|datastore|workmanager' \
  **/*.gradle **/*.gradle.kts **/*.kt 2>/dev/null | head -n 80 || true
echo

echo "== Next commands (manual)"
if [[ -x ./gradlew ]]; then
  echo "try: ./gradlew tasks"
  echo "try: ./gradlew :app:dependencies"
  echo "try: ./gradlew test"
  echo "try: ./gradlew connectedAndroidTest"
else
  echo "no executable ./gradlew found"
fi

