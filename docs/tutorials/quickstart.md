# Quick Start

Get started with Vega Framework in 5 minutes.

## Create Your First Project

### 1. Initialize a New Project

Create a basic project with CLI support:

```bash
vega init my-app
cd my-app
```

Or create a project with FastAPI web support:

```bash
vega init my-api --template fastapi
cd my-api
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Project Structure

Your project will have this structure:

```
my-app/
├── domain/              # Business logic
│   ├── entities/
│   ├── repositories/
│   ├── services/
│   └── interactors/
├── application/         # Workflows
│   └── mediators/
├── infrastructure/      # Implementations
│   ├── repositories/
│   └── services/
├── presentation/        # Interfaces
│   └── cli/
├── config.py           # DI container
├── settings.py         # Settings
└── main.py            # Entry point
```

## Create Your First Components

### 1. Create an Entity

```bash
vega generate entity User
```

Edit `domain/entities/user.py`:

```python
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    email: str
```

### 2. Create a Repository

```bash
vega generate repository UserRepository --impl memory
```

This creates:
- Interface: `domain/repositories/user_repository.py`
- Implementation: `infrastructure/repositories/memory_user_repository.py`

### 3. Create an Interactor (Use Case)

```bash
vega generate interactor CreateUser
```

Edit `domain/interactors/create_user.py`:

```python
from vega.patterns import Interactor
from vega.di import bind
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository

class CreateUser(Interactor[User]):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @bind
    async def call(self, repository: UserRepository) -> User:
        user = User(
            id=generate_id(),
            name=self.name,
            email=self.email
        )
        return await repository.save(user)
```

### 4. Configure DI Container

Edit `config.py`:

```python
from vega.di import Container, set_container
from domain.repositories.user_repository import UserRepository
from infrastructure.repositories.memory_user_repository import MemoryUserRepository

container = Container({
    UserRepository: MemoryUserRepository,
})

set_container(container)
```

### 5. Use Your Interactor

```python
import asyncio
from domain.interactors.create_user import CreateUser
import config  # Initialize DI

async def main():
    user = await CreateUser(name="John Doe", email="john@example.com")
    print(f"Created user: {user.name}")

asyncio.run(main())
```

## What's Next?

- [Project Structure](../explanation/project-structure.md) - Understand the default layout
- [Architecture Guide](../explanation/architecture/clean-architecture.md) - Learn Clean Architecture principles
- [Patterns](../explanation/patterns/interactor.md) - Deep dive into core patterns
- [CLI Commands](../reference/cli/overview.md) - Learn all CLI commands
