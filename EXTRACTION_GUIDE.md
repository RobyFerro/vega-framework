# Vega Framework - Extraction & Publishing Guide

## ✅ Framework Completo

Il framework **Vega** è completo e funzionante. Tutto il codice è in `vega-framework/`.

### Struttura

```
vega-framework/
├── vega/                    # Framework package
│   ├── __init__.py          # Main exports
│   │
│   ├── di/                  # Dependency Injection
│   │   ├── container.py     # IOC Container
│   │   ├── decorators.py    # @bind, @injectable
│   │   ├── scope.py         # Scope management
│   │   └── errors.py
│   │
│   ├── patterns/            # Clean Architecture Patterns
│   │   ├── interactor.py    # Use cases
│   │   ├── mediator.py      # Workflows
│   │   ├── repository.py    # Data persistence
│   │   └── service.py       # External services
│   │
│   ├── settings/            # Settings Management
│   │   └── base.py          # Pydantic settings base
│   │
│   └── cli/                 # CLI Tools ✅ NUOVO!
│       ├── main.py          # CLI entry point
│       └── commands/
│           ├── init.py      # vega init <project>
│           └── generate.py  # vega generate <component>
│
├── pyproject.toml           # Package configuration
└── README.md                # Documentation
```

---

## 🚀 Test Eseguiti

### ✅ 1. TODO App Example
```bash
cd examples/todo_app
python main.py

# Output:
# [*] Creating todos...
# [+] Created: Learn CleanArch Framework
# SUCCESS: CleanArch Framework working perfectly!
```

### ✅ 2. CLI Init Command
```bash
cd vega-framework
PYTHONPATH=. python vega/cli/main.py init test-shop --path=/tmp

# Output:
# [*] Creating Vega project: test-shop
# + Created domain/entities/
# + Created config.py
# SUCCESS: Success! Project created successfully.
```

### ✅ 3. CLI Generate Command
```bash
cd /tmp/test-shop
vega generate entity Product

# Output:
# + Created domain/entities/product.py
```

---

## 📦 Come Estrarre e Pubblicare

### Step 1: Crea Repository Separato

```bash
# Crea nuovo repo GitHub
gh repo create your-org/vega-framework --public

# Copia il framework
cd /path/to/new/repo
cp -r /path/to/vega-core/vega-framework/* .

# Inizializza git
git init
git add .
git commit -m "Initial commit: Vega Framework v0.1.0"
git remote add origin git@github.com:your-org/vega-framework.git
git push -u origin main
```

### Step 2: Pubblica su PyPI

```bash
cd vega-framework

# Install poetry (if not installed)
pip install poetry

# Build package
poetry build

# Publish to PyPI (first time)
poetry config pypi-token.pypi your-pypi-token
poetry publish

# Or publish to test PyPI first
poetry publish -r testpypi
```

### Step 3: Test Installation

```bash
# Install from PyPI
pip install vega-framework

# Test CLI
vega --help
vega init my-app
```

### Step 4: Refactor Vega Core

```bash
cd vega-core

# Add dependency
poetry add vega-framework

# Update imports
# Prima:  from vega_core.di import bind
# Dopo:   from vega.di import bind

# Run tests
poetry run pytest
```

---

## 🎯 Cosa Funziona

### ✅ Dependency Injection
```python
from vega.di import bind, injectable, Scope

@injectable(scope=Scope.SINGLETON)
class EmailService:
    pass

class CreateUser(Interactor[User]):
    @bind
    async def call(self, repo: UserRepository, email: EmailService):
        # Dependencies auto-injected!
        pass
```

### ✅ Clean Architecture Patterns
```python
from vega.patterns import Interactor, Mediator, Repository, Service

# Entity
@dataclass
class Product:
    id: str
    name: str

# Repository Interface
class ProductRepository(Repository[Product]):
    pass

# Use Case
class CreateProduct(Interactor[Product]):
    @bind
    async def call(self, repo: ProductRepository):
        pass

# Workflow
class CheckoutFlow(Mediator[Order]):
    async def call(self):
        product = await CreateProduct(name="...")
        order = await PlaceOrder(product.id)
        return order
```

### ✅ CLI Scaffolding
```bash
# Create new project
vega init my-shop

# Generate components
vega generate entity Product
vega generate repository ProductRepository
vega generate interactor CreateProduct
vega generate mediator CheckoutFlow
```

### ✅ Settings Management
```python
from vega.settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str

settings = Settings()  # Loads from .env
```

---

## 📝 Checklist Pre-Pubblicazione

### Code Quality
- [ ] Remove debug prints
- [ ] Add docstrings to all public APIs
- [ ] Type hints completi
- [ ] Remove TODO comments

### Testing
- [ ] Unit tests per DI system
- [ ] Integration tests per patterns
- [ ] CLI tests
- [ ] Test coverage > 80%

### Documentation
- [x] README.md completo
- [ ] API documentation (Sphinx)
- [ ] Esempi multipli (e-commerce, AI, fintech)
- [ ] Migration guide (vega-core → vega-framework)
- [ ] Contributing guidelines

### Packaging
- [x] pyproject.toml configurato
- [ ] LICENSE file (MIT)
- [ ] CHANGELOG.md
- [ ] Version in `__init__.py`
- [ ] GitHub Actions CI/CD

### Marketing
- [ ] GitHub repo README
- [ ] Twitter/LinkedIn announcement
- [ ] Reddit r/Python post
- [ ] Dev.to article
- [ ] Documentation website

---

## 🎨 Nome Framework

**Opzione A: `vega-framework`** (Raccomandato)
- ✅ Unique, memorable
- ✅ Correlato a vega-core
- ✅ Package: `pip install vega-framework`
- ✅ CLI: `vega init my-app`

**Opzione B: `cleanarch`**
- ❌ Generico
- ✅ Descrittivo
- ✅ SEO-friendly

**Scelta consigliata**: `vega-framework`

---

## 📊 Roadmap

### v0.1.0 (Attuale - MVP) ✅
- [x] DI system completo
- [x] Pattern base (Interactor, Mediator, Repository, Service)
- [x] Scope management (SINGLETON, SCOPED, TRANSIENT)
- [x] Settings base (Pydantic)
- [x] CLI init command
- [x] CLI generate command
- [x] pyproject.toml configurato

### v0.2.0 - Enhanced DX
- [ ] Template multipli (`--template=fastapi`, `--template=ai-rag`)
- [ ] `vega doctor` command (validate architecture)
- [ ] Better error messages
- [ ] Progress bars per init
- [ ] Auto-update config.py quando generi componenti

### v0.3.0 - Plugin Ecosystem
- [ ] `vega-postgres` - PostgreSQL repositories
- [ ] `vega-redis` - Redis cache
- [ ] `vega-fastapi` - FastAPI integration
- [ ] `vega-celery` - Task queue

### v1.0.0 - Production Ready
- [ ] Documentation website
- [ ] 100% test coverage
- [ ] Performance benchmarks
- [ ] Migration tools
- [ ] VS Code extension

---

## 🔥 Quick Start (After Publishing)

```bash
# Install
pip install vega-framework

# Create project
vega init my-shop
cd my-shop
poetry install

# Generate components
vega generate entity Product
vega generate repository ProductRepository
vega generate interactor CreateProduct

# Run
python -c "
from my_shop.domain.interactors.create_product import CreateProduct
import asyncio

async def main():
    product = await CreateProduct(name='Laptop', price=999)
    print(product)

asyncio.run(main())
"
```

---

## 💡 Tips

### Aggiornare il Framework
```bash
# In vega-framework/
# 1. Fai modifiche
# 2. Bump version in pyproject.toml
poetry version patch  # 0.1.0 → 0.1.1
# 3. Rebuild & publish
poetry build
poetry publish
```

### Test Locale Prima di Pubblicare
```bash
# Build
poetry build

# Install locally in altro progetto
cd /path/to/test-project
pip install /path/to/vega-framework/dist/vega_framework-0.1.0-py3-none-any.whl
```

### CI/CD con GitHub Actions
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install poetry
      - run: poetry build
      - run: poetry publish
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
```

---

## ✨ Risultato Finale

Dopo l'estrazione avrai:

1. **Framework Open-Source**
   - PyPI package `vega-framework`
   - GitHub repo con CI/CD
   - Documentation website

2. **Vega Core Più Pulito**
   - Dependency sul framework
   - Codice specifico dominio
   - Facile da mantenere

3. **Community Benefits**
   - Altri possono usare il framework
   - Contributions esterne
   - Showcase per portfolio

**Timeline**: 1 settimana per pubblicazione completa! 🚀
