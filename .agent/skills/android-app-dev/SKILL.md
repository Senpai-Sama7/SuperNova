---
name: android-app-dev
description: Android application development using Android Studio, Kotlin, and Jetpack. Use when creating, modifying, debugging, or optimizing Android apps. Covers project setup, UI development (XML layouts and Jetpack Compose), app architecture (MVVM, ViewModel, LiveData/Flow), data persistence (Room), navigation, testing, performance optimization, Material Design, and Gradle build configuration. Use for all Android development tasks including building new apps from templates, implementing features, refactoring code, writing tests, and troubleshooting build issues.
---

# Android App Development

Comprehensive guidance for building Android applications using Kotlin, Android Studio, and Jetpack libraries.

## Quick Start

### Create New Project
1. File → New → New Project
2. Select template: "Empty Views Activity" (XML) or "Empty Activity" (Compose)
3. Configure:
   - Name: App name
   - Package: Reverse domain (com.example.appname)
   - Language: Kotlin
   - Minimum SDK: API 24+ (Android 7.0) for modern apps
   - Build config: Kotlin DSL (build.gradle.kts)

### Project Structure
```
app/
├── src/main/
│   ├── java/com/package/name/
│   │   ├── MainActivity.kt
│   │   ├── ui/                 # UI layer
│   │   ├── data/               # Data layer (repositories, database)
│   │   └── di/                 # Dependency injection (Hilt modules)
│   ├── res/
│   │   ├── layout/             # XML layouts (Views)
│   │   ├── values/
│   │   │   ├── colors.xml
│   │   │   ├── strings.xml
│   │   │   └── themes.xml
│   │   └── drawable/
│   └── AndroidManifest.xml
├── build.gradle.kts            # Module-level build config
└── src/test/                   # Unit tests
```

## Core Development Workflows

### Building UI

**Jetpack Compose (Recommended for new apps):**
```kotlin
@Composable
fun Greeting(name: String) {
    Text(text = "Hello $name!")
}

@Composable
fun MyApp() {
    MaterialTheme {
        Surface {
            Greeting("Android")
        }
    }
}
```

**XML Layouts (Traditional):**
```xml
<!-- res/layout/activity_main.xml -->
<LinearLayout 
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">
    
    <TextView
        android:id="@+id/textView"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/hello" />
</LinearLayout>
```

### App Architecture (MVVM)

**ViewModel:**
```kotlin
class MyViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    
    fun updateData(data: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(data = data) }
        }
    }
}
```

**Activity/Fragment with ViewModel:**
```kotlin
class MainActivity : ComponentActivity() {
    private val viewModel: MyViewModel by viewModels()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val uiState by viewModel.uiState.collectAsState()
            MyApp(uiState)
        }
    }
}
```

### Data Persistence with Room

**Entity:**
```kotlin
@Entity(tableName = "items")
data class Item(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val name: String,
    val timestamp: Long = System.currentTimeMillis()
)
```

**DAO:**
```kotlin
@Dao
interface ItemDao {
    @Query("SELECT * FROM items ORDER BY timestamp DESC")
    fun observeAll(): Flow<List<Item>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(item: Item)
    
    @Delete
    suspend fun delete(item: Item)
}
```

**Database:**
```kotlin
@Database(entities = [Item::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun itemDao(): ItemDao
}
```

### Navigation

**Compose Navigation:**
```kotlin
@Composable
fun NavGraph() {
    val navController = rememberNavController()
    
    NavHost(navController, startDestination = "home") {
        composable("home") { HomeScreen() }
        composable("detail/{itemId}") { backStackEntry ->
            val itemId = backStackEntry.arguments?.getString("itemId")
            DetailScreen(itemId)
        }
    }
}
```

## Dependency Management

**Add dependencies to app/build.gradle.kts:**
```kotlin
dependencies {
    // Core
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    
    // Compose (optional)
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    
    // Architecture Components
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    
    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    
    // Hilt (DI)
    implementation("com.google.dagger:hilt-android:2.50")
    kapt("com.google.dagger:hilt-compiler:2.50")
    
    // Testing
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
}
```

## Testing

### Unit Tests
```kotlin
@Test
fun `viewModel updates state correctly`() = runTest {
    val viewModel = MyViewModel()
    viewModel.updateData("test")
    
    assertEquals("test", viewModel.uiState.value.data)
}
```

### UI Tests (Compose)
```kotlin
@get:Rule
val composeTestRule = createComposeRule()

@Test
fun greeting_isDisplayed() {
    composeTestRule.setContent {
        Greeting("Android")
    }
    
    composeTestRule.onNodeWithText("Hello Android!").assertIsDisplayed()
}
```

## Build and Run

**Build APK:**
```bash
./gradlew assembleDebug          # Debug APK
./gradlew assembleRelease        # Release APK
```

**Run tests:**
```bash
./gradlew test                   # Unit tests
./gradlew connectedAndroidTest   # Instrumented tests
```

**Install on device:**
```bash
./gradlew installDebug
```

## Common Gradle Configuration

**app/build.gradle.kts:**
```kotlin
android {
    namespace = "com.example.app"
    compileSdk = 34

    defaultConfig {
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    
    buildFeatures {
        compose = true
    }
    
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.8"
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = "17"
    }
}
```

## Material Design 3

**Theme setup:**
```kotlin
@Composable
fun MyAppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) darkColorScheme() else lightColorScheme()
    
    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
```

**Common components:**
```kotlin
Button(onClick = { /* action */ }) {
    Text("Click me")
}

Card {
    Column(modifier = Modifier.padding(16.dp)) {
        Text("Title", style = MaterialTheme.typography.titleLarge)
        Text("Description", style = MaterialTheme.typography.bodyMedium)
    }
}

OutlinedTextField(
    value = text,
    onValueChange = { text = it },
    label = { Text("Label") }
)
```

## Performance Best Practices

- Use `@Composable` functions that are side-effect free
- Avoid unnecessary recompositions with `remember` and `derivedStateOf`
- Load images efficiently with Coil or Glide
- Use `LazyColumn`/`LazyRow` for large lists
- Move heavy work off main thread using `viewModelScope` or `rememberCoroutineScope`
- Enable R8/ProGuard for release builds

## Troubleshooting

**Build issues:**
- Sync Project with Gradle Files (elephant icon)
- Clean build: `./gradlew clean`
- Invalidate caches: File → Invalidate Caches

**Dependency conflicts:**
- Use BOM (Bill of Materials) for Compose
- Check for transitive dependency conflicts with `./gradlew app:dependencies`

**Runtime crashes:**
- Check logcat for stack traces
- Verify AndroidManifest permissions
- Check for null safety issues (Kotlin null pointer exceptions)

## Resources

- Android Developer Documentation: https://developer.android.com
- Kotlin Documentation: https://kotlinlang.org/docs
- Material Design 3: https://m3.material.io
- Android Jetpack: https://developer.android.com/jetpack
