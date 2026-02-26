# Code Smells Catalog

## Bloaters

### Long Method
**Detection:** Method > 50 lines or > 10 logical blocks
**Problem:** Hard to understand, test, and reuse
**Solution:** Extract Method

```python
# Smell
def process_order(order):
    # 100 lines of validation
    # 50 lines of payment processing
    # 30 lines of notification
    # 40 lines of inventory update
    pass

# Refactored
def process_order(order):
    validate_order(order)
    process_payment(order)
    send_notifications(order)
    update_inventory(order)
```

### Large Class
**Detection:** Class > 300 lines or > 10 responsibilities
**Problem:** Multiple reasons to change, violates SRP
**Solution:** Extract Class

```python
# Smell
class UserManager:
    # Authentication methods
    # Profile management
    # Preferences
    # Permissions
    # Notifications
    pass

# Refactored
class AuthenticationService: pass
class ProfileService: pass
class PreferenceService: pass
```

### Primitive Obsession
**Detection:** Primitives used for domain concepts
**Problem:** No type safety, scattered validation
**Solution:** Replace Primitive with Object

```python
# Smell
def create_user(phone: str, email: str):
    # Phone format validated here
    # Email format validated here

# Refactored
@dataclass
class Phone:
    number: str
    
    def __post_init__(self):
        if not validate_phone(self.number):
            raise ValueError("Invalid phone")

@dataclass
class Email:
    address: str
    
    def __post_init__(self):
        if not validate_email(self.address):
            raise ValueError("Invalid email")

def create_user(phone: Phone, email: Email):
    # Already validated!
```

### Long Parameter List
**Detection:** > 4 parameters
**Problem:** Hard to call, easy to swap order
**Solution:** Introduce Parameter Object

```python
# Smell
def create_user(first, last, email, phone, address, city, zip):
    pass

# Refactored
@dataclass
class Address:
    street: str
    city: str
    zip: str

@dataclass
class UserProfile:
    first_name: str
    last_name: str
    email: Email
    phone: Phone
    address: Address

def create_user(profile: UserProfile):
    pass
```

## Object-Orientation Abusers

### Switch Statements
**Detection:** switch/if-elif chains on type
**Problem:** Missed polymorphism, hard to extend
**Solution:** Replace Conditional with Polymorphism

```python
# Smell
def calculate_area(shape):
    if shape.type == "circle":
        return 3.14 * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height
    elif shape.type == "triangle":
        return 0.5 * shape.base * shape.height

# Refactored
class Shape(ABC):
    @abstractmethod
    def area(self): pass

class Circle(Shape):
    def area(self): return 3.14 * self.radius ** 2

class Rectangle(Shape):
    def area(self): return self.width * self.height
```

### Temporary Field
**Detection:** Field only set/used in some methods
**Problem:** Object in inconsistent state
**Solution:** Extract Class or Replace Method with Method Object

```python
# Smell
class ReportGenerator:
    def __init__(self):
        self.temp_data = None  # Only used in generate_report
    
    def generate_report(self, data):
        self.temp_data = process(data)
        # ... use temp_data
        self.temp_data = None

# Refactored
class ReportGenerator:
    def generate_report(self, data):
        processed = self._process_data(data)
        return self._create_report(processed)
```

### Refused Bequest
**Detection:** Subclass ignores or overrides parent methods
**Problem:** Is-a relationship is wrong
**Solution:** Replace Inheritance with Delegation

```python
# Smell
class Bird:
    def fly(self): pass

class Penguin(Bird):
    def fly(self):
        raise Exception("Penguins can't fly!")

# Refactored
class Bird:
    def move(self): pass

class FlyingBird(Bird):
    def fly(self): pass

class Penguin(Bird):
    def swim(self): pass
```

## Change Preventers

### Divergent Change
**Detection:** One class changes for many reasons
**Problem:** Violates SRP
**Solution:** Extract Class

```python
# Smell: User class changes for auth, profile, and notifications
class User:
    def authenticate(self): pass
    def update_profile(self): pass
    def send_notification(self): pass
```

### Shotgun Surgery
**Detection:** One change requires many class edits
**Problem:** Tight coupling
**Solution:** Move Method, Move Field, Inline Class

```python
# Smell: Changing tax calculation requires edits in Order, Invoice, Quote
# Refactored: Centralize in TaxCalculator
```

### Parallel Inheritance Hierarchies
**Detection:** Creating a subclass requires creating another
**Problem:** Tight coupling between hierarchies
**Solution:** Move Method, Move Field

## Dispensables

### Duplicate Code
**Detection:** Same code in multiple places
**Problem:** Change requires multiple edits
**Solution:** Extract Method, Pull Up Method

```python
# Smell
def process_order_a(order):
    validate(order)
    calculate_tax(order)
    save(order)

def process_order_b(order):
    validate(order)
    calculate_tax(order)
    save(order)

# Refactored
process_order = process_order_a  # Same implementation!
```

### Lazy Class
**Detection:** Class does too little
**Problem:** Unnecessary abstraction
**Solution:** Inline Class or Collapse Hierarchy

### Data Class
**Detection:** Class with only fields and accessors
**Problem:** Behavior scattered elsewhere
**Solution:** Move behavior into class

```python
# Smell
@dataclass
class Rectangle:
    width: float
    height: float

# Behavior scattered:
def area(rect): return rect.width * rect.height
def perimeter(rect): return 2 * (rect.width + rect.height)

# Refactored
@dataclass
class Rectangle:
    width: float
    height: float
    
    def area(self): return self.width * self.height
    def perimeter(self): return 2 * (self.width + self.height)
```

### Dead Code
**Detection:** Unused variables, methods, classes
**Problem:** Maintenance burden, confusion
**Solution:** Delete it (it's in version control!)

## Couplers

### Feature Envy
**Detection:** Method uses more features of another class
**Problem:** Wrong place for logic
**Solution:** Move Method

```python
# Smell
class Order:
    def calculate_discount(self):
        if self.customer.loyalty_years > 5:
            return self.total * 0.1
        return 0

# Refactored: Move to Customer
class Customer:
    def get_discount_percent(self):
        return 0.1 if self.loyalty_years > 5 else 0

class Order:
    def calculate_discount(self):
        return self.total * self.customer.get_discount_percent()
```

### Inappropriate Intimacy
**Detection:** Classes too tightly coupled
**Problem:** Hard to change independently
**Solution:** Move Method, Move Field, Change Bidirectional to Unidirectional

### Message Chains
**Detection:** `a.getB().getC().doSomething()`
**Problem:** Fragile, violates Law of Demeter
**Solution:** Hide Delegate

```python
# Smell
address = order.get_customer().get_address().get_zip()

# Refactored
address = order.get_customer_zip()

# In Order class:
def get_customer_zip(self):
    return self.customer.get_zip()
```

### Middle Man
**Detection:** Class only delegates to another
**Problem:** Unnecessary indirection
**Solution:** Remove Middle Man

## Detecting Code Smells

### Automated Detection

| Tool | Language | Smells Detected |
|------|----------|-----------------|
| pylint | Python | Complexity, duplicates |
| radon | Python | Cyclomatic complexity |
| xenon | Python | Code metrics monitoring |
| eslint | JavaScript | Complexity, best practices |
| SonarQube | Multi | Comprehensive |
| CodeClimate | Multi | Maintainability |

### Manual Detection Checklist
- [ ] Methods > 50 lines
- [ ] Classes > 300 lines
- [ ] Methods > 4 parameters
- [ ] Commented-out code
- [ ] TODO/FIXME comments
- [ ] Deep nesting (> 3 levels)
- [ ] Feature envy (other class names dominate)
- [ ] Duplicated logic
