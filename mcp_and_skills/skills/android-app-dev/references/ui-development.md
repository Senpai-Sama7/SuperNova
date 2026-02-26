# UI Development Guide

## Jetpack Compose

### Layout Components

```kotlin
@Composable
fun MyScreen() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text("Header", style = MaterialTheme.typography.headlineMedium)
        
        Row(
            horizontalArrangement = Arrangement.SpaceBetween,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Left")
            Text("Right")
        }
        
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text("Centered")
        }
    }
}
```

### Lazy Lists

```kotlin
@Composable
fun ItemList(items: List<Item>) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(items, key = { it.id }) { item ->
            ItemCard(item)
        }
        
        item {
            Text("End of list")
        }
    }
}

@Composable
fun ItemGrid(items: List<Item>) {
    LazyVerticalGrid(
        columns = GridCells.Adaptive(minSize = 128.dp),
        contentPadding = PaddingValues(16.dp)
    ) {
        items(items) { item ->
            ItemThumbnail(item)
        }
    }
}
```

### State Hoisting

```kotlin
// Stateless composable (reusable)
@Composable
fun ExpandableCard(
    title: String,
    isExpanded: Boolean,
    onExpandToggle: () -> Unit,
    content: @Composable () -> Unit
) {
    Card {
        Column {
            Row(
                modifier = Modifier.clickable { onExpandToggle() }
            ) {
                Text(title)
                Icon(
                    if (isExpanded) Icons.Default.ExpandLess 
                    else Icons.Default.ExpandMore,
                    contentDescription = "Expand"
                )
            }
            if (isExpanded) {
                content()
            }
        }
    }
}

// State holder
@Composable
fun MyExpandableCard() {
    var isExpanded by remember { mutableStateOf(false) }
    
    ExpandableCard(
        title = "Card Title",
        isExpanded = isExpanded,
        onExpandToggle = { isExpanded = !isExpanded }
    ) {
        Text("Expanded content")
    }
}
```

### Navigation

```kotlin
@Composable
fun MyApp() {
    val navController = rememberNavController()
    
    NavHost(navController, startDestination = "home") {
        composable("home") {
            HomeScreen(
                onNavigateToDetail = { id ->
                    navController.navigate("detail/$id")
                }
            )
        }
        composable(
            "detail/{itemId}",
            arguments = listOf(navArgument("itemId") { type = NavType.StringType })
        ) { backStackEntry ->
            val itemId = backStackEntry.arguments?.getString("itemId")
            DetailScreen(itemId)
        }
    }
}
```

## XML Layouts

### Common Layouts

```xml
<!-- ConstraintLayout (flexible, flat hierarchy) -->
<androidx.constraintlayout.widget.ConstraintLayout 
    android:layout_width="match_parent"
    android:layout_height="match_parent">
    
    <TextView
        android:id="@+id/title"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />
    
    <Button
        android:id="@+id/button"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        app:layout_constraintTop_toBottomOf="@id/title"
        app:layout_constraintStart_toStartOf="parent" />
</androidx.constraintlayout.widget.ConstraintLayout>

<!-- LinearLayout (simple, sequential) -->
<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="vertical">
    
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content" />
    <Button android:layout_width="wrap_content" android:layout_height="wrap_content" />
</LinearLayout>
```

### RecyclerView (XML approach)

```kotlin
// Adapter
class ItemAdapter(
    private val onItemClick: (Item) -> Unit
) : ListAdapter<Item, ItemAdapter.ViewHolder>(DiffCallback()) {
    
    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val title: TextView = view.findViewById(R.id.title)
    }
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_layout, parent, false)
        return ViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = getItem(position)
        holder.title.text = item.title
        holder.itemView.setOnClickListener { onItemClick(item) }
    }
    
    class DiffCallback : DiffUtil.ItemCallback<Item>() {
        override fun areItemsTheSame(old: Item, new: Item) = old.id == new.id
        override fun areContentsTheSame(old: Item, new: Item) = old == new
    }
}

// Usage
recyclerView.adapter = ItemAdapter { item ->
    // Handle click
}
recyclerView.layoutManager = LinearLayoutManager(context)
```

## Theming

### Material 3 Theme

```kotlin
private val DarkColorScheme = darkColorScheme(
    primary = Purple80,
    secondary = PurpleGrey80,
    tertiary = Pink80
)

private val LightColorScheme = lightColorScheme(
    primary = Purple40,
    secondary = PurpleGrey40,
    tertiary = Pink40
)

@Composable
fun MyAppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    
    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
```

### Dynamic Colors (Android 12+)

```kotlin
val colorScheme = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
    val context = LocalContext.current
    if (darkTheme) dynamicDarkColorScheme(context) 
    else dynamicLightColorScheme(context)
} else {
    if (darkTheme) DarkColorScheme else LightColorScheme
}
```

## Animation

```kotlin
// Simple visibility animation
var visible by remember { mutableStateOf(true) }
AnimatedVisibility(visible = visible) {
    Text("Hello")
}

// Content change animation
Crossfade(targetState = currentScreen) { screen ->
    when (screen) {
        Screen.Home -> HomeScreen()
        Screen.Profile -> ProfileScreen()
    }
}

// Value animation
val animatedProgress by animateFloatAsState(
    targetValue = if (loading) 1f else 0f,
    animationSpec = tween(durationMillis = 300)
)
```
