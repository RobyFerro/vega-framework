# Correzioni Documentazione

## Discrepanze Trovate tra Codice e Docs

### 1. SERVICES Pattern ❌ CRITICO
**Problema**: La documentazione usa `Container({...})` inline
**Codice reale**: Usa `SERVICES = {...}` poi `Container(SERVICES)`

**Template reale** (`config.py.j2`):
```python
SERVICES = {
    # UserRepository: MemoryUserRepository,
}
container = Container(SERVICES)
set_container(container)
```

**File da correggere**:
- `docs/core/dependency-injection.md` - Tutti gli esempi
- `docs/philosophy.md` - Sezione DI
- `docs/architecture/*.md` - Esempi Container
- `docs/getting-started/project-structure.md` - Config section
- `docs/guides/building-domain-layer.md` - Config examples
- `README.md` - Quick start example

**Azione**: Sostituire tutti i `Container({...})` con pattern SERVICES

---

### 2. Component Types nel CLI ⚠️  IMPORTANTE
**Problema**: Documentazione manca alcuni component types

**Component types reali** (da `cli/main.py`):
- entity
- repository / repo (alias)
- service
- interactor
- mediator
- router
- middleware
- webmodel (con --request / --response)
- model (SQLAlchemy)
- command
- event ✅ **MANCA NELLE DOCS**
- event-handler / subscriber ✅ **MANCA NELLE DOCS**

**File da aggiornare**:
- `docs/cli/generate.md` - Aggiungere event e event-handler
- `docs/cli/overview.md` - Tabella completa

---

### 3. Mediator Metaclass 📝 INFO
**Codice reale**: `async def __call__(cls, *args, **kwargs)`

Il Mediator ha metaclass con `__call__` async. La docs è corretta su questo.

---

### 4. Repository Base Class 📝 INFO
**Codice reale**: `Repository[T]` è una classe vuota (ABC, Generic[T])
**Non ha metodi base** come `find_by_id`, `save`, ecc.

La documentazione dovrebbe chiarire che:
- `Repository[T]` è solo un marker/base type
- I metodi CRUD vanno definiti nelle interfacce concrete
- **Roadmap menziona** aggiunta di BaseRepository con CRUD

---

### 5. Interactor e @bind 📝 INFO
**Template reale**:
```python
@bind
async def call(self) -> dict:  # Add dependencies as parameters
```

La documentazione è corretta - `@bind` inietta dependencies come parametri.

---

## Priorità Correzioni

### Priorità 1 - CRITICO
1. ✅ Sostituire pattern Container inline con SERVICES in TUTTI i file docs
2. ✅ Aggiornare README.md con pattern SERVICES

### Priorità 2 - IMPORTANTE
3. ✅ Aggiungere `event` e `event-handler` a docs/cli/generate.md
4. ✅ Aggiornare tabella component types in docs/cli/overview.md

### Priorità 3 - MIGLIORAMENTI
5. ✅ Chiarire che Repository[T] è vuota (no metodi base)
6. ✅ Linkare a Roadmap per BaseRepository futuro

---

## Pattern di Sostituzione

### Pattern CORRETTO (da usare ovunque):

```python
# config.py
from vega.di import Container, set_container

# Domain interfaces
from domain.repositories.user_repository import UserRepository

# Infrastructure implementations
from infrastructure.repositories.postgres_user_repository import PostgresUserRepository

# DI Registry: Map interfaces to implementations
SERVICES = {
    UserRepository: PostgresUserRepository,
}

# Create and set container
container = Container(SERVICES)
set_container(container)
```

### Per esempi di test (può rimanere inline per brevità):
```python
# Test - inline OK per semplicità
test_container = Container({
    UserRepository: MockUserRepository,
})
set_container(test_container)
```

---

## Status Correzioni

- [ ] docs/core/dependency-injection.md
- [ ] docs/philosophy.md
- [ ] docs/architecture/clean-architecture.md
- [ ] docs/architecture/layers.md
- [ ] docs/architecture/dependency-rule.md
- [ ] docs/getting-started/project-structure.md
- [ ] docs/guides/building-domain-layer.md
- [ ] README.md
- [ ] docs/cli/generate.md (aggiungere event/event-handler)
- [ ] docs/cli/overview.md (tabella component types)
