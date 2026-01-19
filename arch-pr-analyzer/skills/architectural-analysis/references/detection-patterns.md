## Detection Patterns for Architectural Elements

This reference provides comprehensive patterns for detecting architectural elements across different frameworks, languages, and patterns.

## Dependency Detection Patterns

### Python

**Import statements:**
```python
import module_name
from package import module
from package.subpackage import Class, function
import package as alias
```

**Detection regex:**
```regex
^import\s+(\S+)(?:\s+as\s+\S+)?$
^from\s+(\S+)\s+import\s+(.+)$
```

**Parsing strategy:**
1. Extract module/package name before `import` or after `from`
2. Handle `as` aliases (ignore alias, keep original)
3. For `from X import Y`, the dependency is on `X`
4. Track both direct imports and transitive dependencies

### JavaScript/TypeScript

**Import statements:**
```javascript
import X from 'module'
import { A, B } from 'module'
import * as X from 'module'
const X = require('module')
```

**Detection regex:**
```regex
import\s+.*\s+from\s+['"](.+)['"]
require\(['"](.+)['"]\)
```

**Parsing strategy:**
1. Extract module name from string literal
2. Distinguish local imports (./...) from package imports
3. Handle scoped packages (@org/package)
4. Track CommonJS (require) and ES6 (import) patterns

### Java

**Import statements:**
```java
import com.package.Class;
import com.package.*;
import static com.package.Class.method;
```

**Detection regex:**
```regex
^import\s+(static\s+)?([a-zA-Z0-9_.]+)(\.\*)?;$
```

**Parsing strategy:**
1. Extract fully qualified package name
2. Handle wildcard imports (.*) as package-level dependency
3. Track static imports separately
4. Map to package hierarchy

### Go

**Import statements:**
```go
import "package/path"
import (
    "package1"
    alias "package2"
)
```

**Detection regex:**
```regex
import\s+"(.+)"
^\s*(?:(\w+)\s+)?"(.+)"$  // within import block
```

**Parsing strategy:**
1. Extract package path from string
2. Handle import blocks
3. Track aliases
4. Map to Go module structure

## API Endpoint Detection Patterns

### Flask (Python)

**Route decorators:**
```python
@app.route('/path', methods=['GET', 'POST'])
@app.route('/path/<int:id>', methods=['PUT', 'DELETE'])
@blueprint.route('/path')
```

**Detection:**
- Pattern: `@(?:app|blueprint|\w+)\.route\(['"]([^'"]+)['"](?:,\s*methods\s*=\s*\[(.*?)\])?)`
- Extract: path, HTTP methods (default: ['GET'])
- Track: handler function name (next function definition)

### FastAPI (Python)

**Route decorators:**
```python
@router.get("/path")
@router.post("/path")
@app.get("/users/{user_id}")
@app.put("/items/{item_id}", response_model=Item)
```

**Detection:**
- Pattern: `@(?:app|router|\w+)\.(get|post|put|delete|patch|options|head)\(['"]([^'"]+)['"]`
- Extract: HTTP method (from decorator name), path
- Track: type hints, response models

### Express (JavaScript)

**Route definitions:**
```javascript
app.get('/path', handler)
app.post('/path', middleware, handler)
router.put('/path/:id', handler)
app.use('/prefix', router)
```

**Detection:**
- Pattern: `(?:app|router)\.(?:get|post|put|delete|patch|all)\(['"]([^'"]+)['"]`
- Extract: HTTP method, path pattern
- Handle: route parameters (:param), middleware chains

### Django (Python)

**URL patterns:**
```python
path('api/users/', views.user_list, name='user-list')
path('api/users/<int:pk>/', views.user_detail)
re_path(r'^api/items/(?P<pk>[0-9]+)/$', views.item_detail)
```

**Detection:**
- Pattern: `(?:path|re_path)\(['"]([^'"]+)['"],\s*([^,]+)`
- Extract: URL pattern, view function
- Handle: path converters (<int:pk>), regex patterns

### Spring Boot (Java)

**Controller annotations:**
```java
@GetMapping("/users")
@PostMapping("/users")
@PutMapping("/users/{id}")
@RequestMapping(value = "/items", method = RequestMethod.GET)
```

**Detection:**
- Pattern: `@(Get|Post|Put|Delete|Patch)Mapping\(['"]([^'"]+)['"]`
- Pattern: `@RequestMapping\(.*?value\s*=\s*['"]([^'"]+)['"].*?method\s*=\s*RequestMethod\.(\w+)`
- Extract: HTTP method, path
- Track: class-level @RequestMapping for path prefixes

## Database Schema Change Detection

### Migration File Patterns

**Alembic (Python):**
- File pattern: `alembic/versions/*.py`
- Revision pattern: `revision = '[a-f0-9]+'`
- Operations: `op.create_table()`, `op.add_column()`, `op.alter_column()`, `op.drop_column()`

**Django:**
- File pattern: `*/migrations/[0-9]{4}_*.py`
- Operations class: `class Migration(migrations.Migration):`
- Operations: `migrations.CreateModel()`, `migrations.AddField()`, `migrations.AlterField()`, `migrations.RemoveField()`

**Sequelize (JavaScript):**
- File pattern: `migrations/*-*.js`
- Methods: `queryInterface.createTable()`, `queryInterface.addColumn()`, `queryInterface.changeColumn()`, `queryInterface.removeColumn()`

**Prisma:**
- File pattern: `prisma/migrations/*/migration.sql`
- SQL operations: `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`
- Schema file: `prisma/schema.prisma` - `model` definitions

**Flyway (Java):**
- File pattern: `db/migration/V*__*.sql`
- SQL scripts with version numbers
- Detect operations by parsing SQL

### ORM Model Change Detection

**SQLAlchemy (Python):**
```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    # Relationships
    posts = relationship('Post', back_populates='author')
```

**Detection:**
- Class inherits from `Base` or `DeclarativeBase`
- `__tablename__` attribute defines table
- `Column()` defines fields
- `relationship()` defines associations
- Track: column additions, removals, type changes, constraint changes

**Django ORM:**
```python
class User(models.Model):
    email = models.EmailField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    # Relationships
    profile = models.OneToOneField('Profile', on_delete=models.CASCADE)
```

**Detection:**
- Class inherits from `models.Model`
- Fields are `models.*Field()` instances
- Track: field additions, removals, field type changes, relationship changes

**Prisma (TypeScript):**
```prisma
model User {
  id    Int     @id @default(autoincrement())
  email String  @unique
  posts Post[]
}
```

**Detection:**
- `model` keyword
- Field definitions with types
- Attributes: `@id`, `@unique`, `@default`
- Relationships: type references to other models

**TypeORM (TypeScript):**
```typescript
@Entity()
class User {
    @PrimaryGeneratedColumn()
    id: number;

    @Column({ type: 'varchar', length: 255 })
    email: string;

    @OneToMany(() => Post, post => post.author)
    posts: Post[];
}
```

**Detection:**
- `@Entity()` decorator
- `@Column()`, `@PrimaryGeneratedColumn()` decorators
- `@OneToMany`, `@ManyToOne`, `@ManyToMany` for relationships
- Track decorator changes, type changes

## Component Boundary Detection

### Directory Structure Patterns

**Monorepo structure:**
```
packages/
  frontend/
    package.json
  backend/
    package.json
  shared/
    package.json
```

Detection: Presence of `package.json` at each level indicates component boundary

**Python package structure:**
```
src/
  auth/
    __init__.py
  api/
    __init__.py
  data/
    __init__.py
```

Detection: `__init__.py` files mark package boundaries

**Microservice structure:**
```
services/
  auth-service/
    Dockerfile
    package.json
  payment-service/
    Dockerfile
    requirements.txt
```

Detection: Each service has own deployment manifest (Dockerfile) and dependency file

### Deployment Unit Detection

**Indicators of separate deployment units:**

**Docker:**
- `Dockerfile` presence
- `docker-compose.yml` service definitions
- Each service in compose file = deployment unit

**Kubernetes:**
- `deployment.yaml`, `service.yaml` files
- Each Deployment resource = deployment unit
- Namespace boundaries

**Cloud Functions:**
- `serverless.yml`, `functions.yaml`
- Each function definition = deployment unit

**Package manifests:**
- `package.json` (Node.js)
- `requirements.txt`, `pyproject.toml` (Python)
- `pom.xml`, `build.gradle` (Java)
- `go.mod` (Go)
- `Cargo.toml` (Rust)

### Inter-Service Communication Patterns

**HTTP/REST API calls:**
```python
requests.get('http://auth-service/api/validate')
fetch('https://api.example.com/users')
```

Detection: HTTP client calls to other services (different host/service name)

**gRPC calls:**
```python
channel = grpc.insecure_channel('payment-service:50051')
stub = PaymentServiceStub(channel)
```

Detection: gRPC channel creation, service stubs

**Message Queue producers/consumers:**
```python
# Kafka
producer.send('user.events', message)
consumer.subscribe(['order.events'])

# RabbitMQ
channel.basic_publish(exchange='events', routing_key='user.created')

# AWS SQS
sqs.send_message(QueueUrl='...', MessageBody='...')
```

Detection: Message queue client usage, topic/queue names

**Service Mesh:**
```yaml
# Istio VirtualService
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: auth-service
spec:
  hosts:
  - auth-service
```

Detection: Service mesh configuration files

## Data Flow Pattern Detection

### Entry Point Identification

**API endpoints:** (see API detection patterns above)

**Event handlers:**
```python
# AWS Lambda
def lambda_handler(event, context):
    ...

# Celery task
@app.task
def process_order(order_id):
    ...

# Django signals
@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    ...
```

**CLI commands:**
```python
# Click
@click.command()
def deploy():
    ...

# argparse
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    ...
```

**Background jobs:**
```python
# APScheduler
@scheduler.scheduled_job('cron', hour=0)
def daily_cleanup():
    ...

# Cron syntax in comments
# cron: 0 0 * * * script.py
```

### Call Chain Tracing

**Function call detection:**
- Parse function definitions
- Track function calls within bodies
- Build call graph: `function_a() -> [function_b(), function_c()]`

**Method chaining:**
```python
user.orders.filter(status='pending').update(status='processed')
```

Track: Object method calls, query builders

**Async/await patterns:**
```javascript
const user = await fetchUser(id);
const orders = await user.getOrders();
```

Track: Async function calls, promise chains

## Advanced Detection Techniques

### Circular Dependency Detection

**Algorithm:**
1. Build complete dependency graph
2. Run depth-first search (DFS) from each node
3. Track visited nodes and path
4. If revisiting node in current path → circular dependency found
5. Report cycle: `A → B → C → A`

### Breaking Change Detection

**API breaking changes:**
- Endpoint removed (existed in base, not in head)
- Required parameter added
- Response schema incompatible change
- HTTP method changed

**Schema breaking changes:**
- Column dropped (data loss)
- Column type changed incompatibly (string → int)
- NOT NULL constraint added without default
- Unique constraint added (may fail on existing data)

**Dependency breaking changes:**
- Major version upgrade (semantic versioning)
- Removed public API/class/function
- Changed function signature (different parameters)

### Performance Impact Detection

**Index changes:**
- New index: Potential query performance improvement
- Dropped index: Potential query performance regression
- Track: Tables with high write volume (indexes slow writes)

**N+1 query patterns:**
- Loop with database call inside
- Missing eager loading / batch loading

**Large data migrations:**
- `UPDATE` statements on entire tables
- Data backfills in migration scripts
- Flag as potentially long-running

## Language-Specific Nuances

### Python

- Absolute vs relative imports: `from package import X` vs `from . import X`
- Dynamic imports: `importlib.import_module()`
- Namespace packages: multiple packages with same name

### JavaScript/TypeScript

- CommonJS vs ES6 modules: `require()` vs `import`
- Dynamic imports: `import()` function
- Re-exports: `export * from 'module'`
- Type-only imports: `import type { X } from 'module'`

### Java

- Wildcard imports: `import package.*`
- Static imports: `import static Class.method`
- Package private: default access level

### Go

- Standard library vs third-party: path structure
- Internal packages: `/internal/` directory
- Vendoring: `/vendor/` directory

## Best Practices for Detection

1. **Use multiple patterns:** Different codebases use different conventions
2. **Handle edge cases:** Dynamic imports, conditional requires, etc.
3. **Parse carefully:** Respect language syntax (strings, comments)
4. **Validate results:** Cross-check detected patterns
5. **Provide context:** Show where patterns were found (file:line)
6. **Track confidence:** Note when detection is uncertain
7. **Support extensions:** Allow custom pattern definitions

## Testing Detection Patterns

**Create test cases for:**
- Standard patterns (happy path)
- Edge cases (unusual syntax)
- Multiple frameworks in same file
- Commented-out code (should ignore)
- String literals containing pattern-like text (false positives)
- Minified/obfuscated code
- Generated code

**Validate against known codebases:**
- Run detection on popular open-source projects
- Compare results with manual analysis
- Refine patterns based on false positives/negatives
