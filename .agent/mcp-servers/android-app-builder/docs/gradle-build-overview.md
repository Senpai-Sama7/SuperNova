# Gradle Build Overview
Source: https://developer.android.com/build/gradle-build-overview

## What is a Build
A build system transforms source code into an executable application. Gradle uses a task-based approach. Plugins define tasks and their configuration. The Android Gradle Plugin (AGP) registers tasks for building APKs or Android Libraries.

## Build Phases
1. **Initialization**: Determines projects/subprojects, sets up classpaths
2. **Configuration**: Registers tasks, executes build files, applies user build specification
3. **Execution**: Runs out-of-date tasks in DAG order

## Configuration DSL
- Kotlin DSL (recommended) or Groovy DSL
- Declarative approach: specify *what* to build, not *how*
- Example: android { namespace, compileSdk, defaultConfig { applicationId, minSdk, targetSdk } }

## External Dependencies
- Maven repository system: group:artifact:version
- Public and company repositories
- Modularize into subprojects for build time and separation of concerns

## Build Variants
- Composed of build types and product flavors
- Build types: release (optimized, signed) and debug (debuggable, fast build)
- Product flavors: e.g., "demo"/"full" or "free"/"paid"
- Variants named: <flavor><Buildtype> (e.g., demoRelease, fullDebug)
