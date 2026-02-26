# App Architecture Guide

## MVVM Pattern (Model-View-ViewModel)

### Layer Responsibilities

**UI Layer (Activity/Fragment/Composable):**
- Display data
- Handle user input
- Observe ViewModel state
- No business logic

**ViewModel:**
- Expose UI state
- Handle user actions
- Business logic
- Survives configuration changes

**Data Layer (Repository):**
- Single source of truth
- Data operations
- Abstract data sources (DB, network)

**Model:**
- Data classes
- Entities

### Implementation

**ViewModel with StateFlow:**
```kotlin
class TaskViewModel(
    private val repository: TaskRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(TaskUiState())
    val uiState: StateFlow<TaskUiState> = _uiState.asStateFlow()
    
    init {
        viewModelScope.launch {
            repository.observeTasks()
                .collect { tasks ->
                    _uiState.update { it.copy(tasks = tasks) }
                }
        }
    }
    
    fun addTask(title: String) {
        viewModelScope.launch {
            repository.addTask(Task(title = title))
        }
    }
}

data class TaskUiState(
    val tasks: List<Task> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)
```

**Repository Pattern:**
```kotlin
class TaskRepository(
    private val taskDao: TaskDao,
    private val apiService: ApiService
) {
    fun observeTasks(): Flow<List<Task>> = taskDao.observeAll()
    
    suspend fun addTask(task: Task) {
        taskDao.insert(task)
        // Optionally sync with server
    }
    
    suspend fun syncWithServer() {
        val remoteTasks = apiService.fetchTasks()
        taskDao.insertAll(remoteTasks)
    }
}
```

## Hilt Dependency Injection

**Setup:**
```kotlin
// Application class
@HiltAndroidApp
class MyApplication : Application()

// Activity
@AndroidEntryPoint
class MainActivity : ComponentActivity()

// ViewModel
@HiltViewModel
class MyViewModel @Inject constructor(
    private val repository: TaskRepository
) : ViewModel()
```

**Module:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "app_database"
        ).build()
    }
    
    @Provides
    fun provideTaskDao(database: AppDatabase): TaskDao = database.taskDao()
}
```

## Lifecycle Awareness

**LifecycleEventObserver:**
```kotlin
class MyObserver : LifecycleEventObserver {
    override fun onStateChanged(source: LifecycleOwner, event: Lifecycle.Event) {
        when (event) {
            Lifecycle.Event.ON_RESUME -> startLocationUpdates()
            Lifecycle.Event.ON_PAUSE -> stopLocationUpdates()
            else -> { }
        }
    }
}

// Usage
lifecycle.addObserver(MyObserver())
```

**Flow collection with lifecycle:**
```kotlin
// Automatically stops collecting when not visible
viewModel.uiState
    .flowWithLifecycle(lifecycle, Lifecycle.State.STARTED)
    .collect { state ->
        updateUi(state)
    }
```

## State Management

**Remember vs RememberSaveable:**
```kotlin
@Composable
fun MyScreen() {
    // Survives recomposition
    var count by remember { mutableIntStateOf(0) }
    
    // Survives configuration changes and process death
    var text by rememberSaveable { mutableStateOf("") }
}
```

**Derived State:**
```kotlin
// Only recalculates when dependencies change
val filteredList by remember(items, query) {
    derivedStateOf {
        items.filter { it.contains(query, ignoreCase = true) }
    }
}
```

## Best Practices

1. **Single source of truth** - Data flows from repository to UI
2. **Unidirectional data flow** - Events flow up, state flows down
3. **ViewModel survives config changes** - Store UI state in ViewModel
4. **Repository abstracts data sources** - UI doesn't know where data comes from
5. **Use coroutines for async work** - Avoid callbacks
6. **Collect flows with lifecycle awareness** - Prevent leaks
