# Kotlin Basics for Android

## Variables

**Read-only (val) vs Mutable (var):**
```kotlin
val name: String = "Android"  // Cannot be reassigned
var count: Int = 0           // Can be reassigned

// Type inference
val message = "Hello"  // Compiler infers String type
```

## Null Safety

Kotlin's type system distinguishes between nullable and non-nullable types:
```kotlin
var name: String = "Android"
name = null  // Compilation error

var nullableName: String? = "Android"
nullableName = null  // OK

// Safe call operator
val length = nullableName?.length  // Returns null if nullableName is null

// Elvis operator
val displayName = nullableName ?: "Default"

// Not-null assertion (use sparingly)
val forcedLength = nullableName!!.length  // Throws NPE if null
```

## Functions

```kotlin
// Basic function
fun greet(name: String): String {
    return "Hello, $name"
}

// Single-expression function
fun greet(name: String) = "Hello, $name"

// Default parameters
fun greet(name: String, greeting: String = "Hello") = "$greeting, $name"

// Named arguments
greet(greeting = "Hi", name = "Android")

// Extension functions
fun String.addExclamation() = "$this!"
"Hello".addExclamation()  // "Hello!"
```

## Classes and Objects

```kotlin
// Data class (auto-generates equals, hashCode, toString, copy)
data class User(
    val id: String,
    val name: String,
    val email: String
)

// Class with constructor
class Person(val name: String, var age: Int) {
    fun birthday() {
        age++
    }
}

// Sealed class (restricted hierarchy)
sealed class Result
class Success(val data: String) : Result()
class Error(val message: String) : Result()

// Object (singleton)
object Database {
    fun connect() { }
}

// Companion object
class Factory {
    companion object {
        fun create() = Factory()
    }
}
```

## Collections

```kotlin
// List
val immutableList = listOf("a", "b", "c")
val mutableList = mutableListOf("a", "b", "c")

// Map
val map = mapOf("key" to "value", "id" to "123")

// Set
val set = setOf("a", "b", "c")

// Higher-order functions
val numbers = listOf(1, 2, 3, 4, 5)
val doubled = numbers.map { it * 2 }        // [2, 4, 6, 8, 10]
val evens = numbers.filter { it % 2 == 0 }  // [2, 4]
val sum = numbers.reduce { acc, i -> acc + i }  // 15
```

## Coroutines

```kotlin
import kotlinx.coroutines.*

// Launch a coroutine
lifecycleScope.launch {
    // Background work
    val result = withContext(Dispatchers.IO) {
        // Network or database call
        fetchData()
    }
    // Update UI
    updateUi(result)
}

// Suspend function
suspend fun fetchData(): String {
    delay(1000)  // Non-blocking delay
    return "Data"
}

// Flow for streams of data
fun observeData(): Flow<List<Item>> = flow {
    while (true) {
        emit(fetchItems())
        delay(1000)
    }
}

// Collect flow
lifecycleScope.launch {
    viewModel.uiState.collect { state ->
        updateUi(state)
    }
}
```

## Scope Functions

```kotlin
// let - transform and return result
val result = name?.let { 
    it.uppercase() 
}

// run - execute block and return result
val result = person.run {
    "$name is $age years old"
}

// with - operate on object without null check
with(person) {
    println(name)
    println(age)
}

// apply - configure object and return it
val person = Person().apply {
    name = "John"
    age = 30
}

// also - perform side effect and return object
val list = mutableListOf(1, 2, 3).also {
    println("Created list: $it")
}
```
