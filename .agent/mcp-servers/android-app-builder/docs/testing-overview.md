# Testing on Android
Source: https://developer.android.com/training/testing

## Why Test
- Rapid feedback on failures
- Early failure detection in development cycle
- Safer code refactoring
- Stable development velocity, minimizes technical debt

## Test Types
- **Local unit tests**: Run on host JVM (fast, no device needed)
- **Instrumented tests**: Run on devices or emulators
- **UI tests**: Behavior tests and Screenshot tests
- **Robolectric**: Local tests with Android framework simulation

## Testing Libraries
- JUnit4 with AndroidX Test
- AndroidJUnitRunner
- Espresso: UI testing framework (basics, intents, lists, web, accessibility)
- UI Automator: Cross-app UI testing

## Testing Topics
- Fundamentals of testing Android apps
- Test doubles (mocks, fakes, stubs)
- Testing strategies
- Testing different screen sizes
- Content providers and services testing
- Continuous integration basics and automation

## Key Resources
- Android testing samples: github.com/android/testing-samples
- Now In Android demo app: github.com/android/nowinandroid
