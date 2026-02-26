# Testing Guide

## Test Types

### Unit Tests

Location: `src/test/java/`
Run on: JVM (no Android framework)

```kotlin
class CalculatorTest {
    
    @Test
    fun `addition returns correct sum`() {
        val calculator = Calculator()
        val result = calculator.add(2, 3)
        assertEquals(5, result)
    }
    
    @Test
    fun `division by zero throws exception`() {
        val calculator = Calculator()
        assertThrows(ArithmeticException::class.java) {
            calculator.divide(1, 0)
        }
    }
}
```

### ViewModel Tests

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class MyViewModelTest {
    
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()
    
    private val repository: TaskRepository = mock()
    private lateinit var viewModel: TaskViewModel
    
    @Before
    fun setup() {
        viewModel = TaskViewModel(repository)
    }
    
    @Test
    fun `loadTasks updates ui state`() = runTest {
        // Given
        val tasks = listOf(Task("1", "Task 1"))
        whenever(repository.observeTasks()).thenReturn(flowOf(tasks))
        
        // When
        viewModel.loadTasks()
        
        // Then
        assertEquals(tasks, viewModel.uiState.value.tasks)
    }
}

// Test dispatcher rule
@ExperimentalCoroutinesApi
class MainDispatcherRule : TestWatcher() {
    private val testDispatcher = StandardTestDispatcher()
    
    override fun starting(description: Description?) {
        Dispatchers.setMain(testDispatcher)
    }
    
    override fun finished(description: Description?) {
        Dispatchers.resetMain()
    }
}
```

### UI Tests (Compose)

Location: `src/androidTest/java/`

```kotlin
@HiltAndroidTest
class MyAppTest {
    
    @get:Rule(order = 0)
    val hiltRule = HiltAndroidRule(this)
    
    @get:Rule(order = 1)
    val composeTestRule = createAndroidComposeRule<MainActivity>()
    
    @Test
    fun addTask_showsInList() {
        // Type task name
        composeTestRule
            .onNodeWithContentDescription("Task name")
            .performTextInput("New Task")
        
        // Click add button
        composeTestRule
            .onNodeWithText("Add")
            .performClick()
        
        // Verify task appears
        composeTestRule
            .onNodeWithText("New Task")
            .assertIsDisplayed()
    }
    
    @Test
    fun completeTask_showsStrikeThrough() {
        composeTestRule
            .onNodeWithTag("task-checkbox")
            .performClick()
        
        composeTestRule
            .onNodeWithText("Task name")
            .assertTextStyle { style ->
                style.textDecoration == TextDecoration.LineThrough
            }
    }
}
```

### Repository Tests

```kotlin
class TaskRepositoryTest {
    
    private lateinit var database: AppDatabase
    private lateinit var taskDao: TaskDao
    private lateinit var repository: TaskRepository
    
    @Before
    fun setup() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
        
        taskDao = database.taskDao()
        repository = TaskRepository(taskDao)
    }
    
    @After
    fun tearDown() {
        database.close()
    }
    
    @Test
    fun insertAndRetrieveTask() = runTest {
        val task = Task("1", "Test Task")
        
        repository.addTask(task)
        val tasks = repository.observeTasks().first()
        
        assertEquals(1, tasks.size)
        assertEquals("Test Task", tasks[0].title)
    }
}
```

### End-to-End Tests

```kotlin
@RunWith(AndroidJUnit4::class)
@LargeTest
class AppNavigationTest {
    
    @get:Rule
    val activityRule = ActivityTestRule(MainActivity::class.java)
    
    @Test
    fun navigateToDetailAndBack() {
        // Click on first item
        onView(withId(R.id.recycler_view))
            .perform(actionOnItemAtPosition<RecyclerView.ViewHolder>(0, click()))
        
        // Verify detail screen
        onView(withId(R.id.detail_title))
            .check(matches(isDisplayed()))
        
        // Press back
        pressBack()
        
        // Verify home screen
        onView(withId(R.id.recycler_view))
            .check(matches(isDisplayed()))
    }
}
```

## Test Dependencies

```kotlin
dependencies {
    // Unit tests
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.mockito:mockito-core:5.8.0")
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.2.1")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    testImplementation("app.cash.turbine:turbine:1.0.0")
    
    // UI tests
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("com.google.dagger:hilt-android-testing:2.50")
    kaptAndroidTest("com.google.dagger:hilt-compiler:2.50")
}
```

## Running Tests

```bash
# Unit tests
./gradlew test

# UI tests
./gradlew connectedAndroidTest

# Specific test class
./gradlew test --tests "com.example.MyViewModelTest"

# With coverage
./gradlew testDebugUnitTestCoverage
```
