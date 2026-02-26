# App Performance Guide
Source: https://developer.android.com/topic/performance/overview

## Goals
Apps should launch quickly, render smoothly, and require little memory and battery usage.

## Inspect Performance
- Android Studio Profilers (CPU, memory, network, energy)
- System tracing (capture, navigate, custom events)
- Benchmarking: Macrobenchmark (startup, scrolling jank) and Microbenchmark (code-level)
- JankStats library for monitoring jank

## Improve Performance
- R8 app optimizer (shrinking, obfuscation, optimization)
- Baseline Profiles: quickest way to improve performance
- Startup Profiles and DEX layout optimizations
- App startup analysis and optimization

## Common Performance Problems
- **App Startup**: Analyze and optimize launch time
- **ANRs**: Keep app responsive, diagnose and fix ANRs
- **Rendering**: Reduce overdraw, optimize view hierarchies, profile GPU rendering
- **Memory**: Memory management, allocation tracking, leak detection
- **Battery**: Doze/standby optimization, battery monitoring, background optimizations
- **App Size**: Reduce APK size

## Monitoring
- Android vitals: ANRs, crashes, slow rendering, LMKs, wake locks, battery usage
- App Performance Score quiz with actionable insights

## Best Practices
- Use Baseline Profiles for production performance
- Profile with Macrobenchmark for startup and scroll performance
- Monitor with JankStats in production
- SQLite performance best practices
