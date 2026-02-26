# Android Studio Introduction
Source: https://developer.android.com/studio/intro

Android Studio is the official IDE for Android app development, based on IntelliJ IDEA.

## Key Features
- Flexible Gradle-based build system
- Fast and feature-rich emulator
- Unified environment for all Android devices
- Live Edit for composables in real time
- Code templates and GitHub integration
- Extensive testing tools and frameworks
- Lint tools for performance, usability, version compatibility
- C++ and NDK support

## Project Structure
Each project contains modules with source code and resource files:
- Android app modules, Library modules, Google App Engine modules
- manifests: AndroidManifest.xml
- java: Kotlin and Java source code, including JUnit test code
- res: Non-code resources (UI strings, bitmap images)

## Gradle Build System
- Build files: build.gradle.kts (Kotlin recommended) or build.gradle (Groovy)
- Build variants: release and debug build types
- Multiple APK support based on screen density or ABI
- Resource shrinking removes unused resources
- Dependencies managed via Maven repositories

## Debug and Profile Tools
- Inline debugging with variable values, return values, lambda expressions
- Performance profilers for memory, CPU, graphics, network
- Heap dump analysis for memory leaks
- Memory Profiler for allocation tracking
- Code inspections via lint checks and IntelliJ inspections
- Annotations for null pointer and resource type validation
- Logcat for log messages
