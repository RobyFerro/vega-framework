# Quick Start - Vega Framework Testing

Guida rapida per iniziare a scrivere e eseguire test nel framework Vega.

## 🚀 Setup Veloce

```bash
# 1. Installa le dipendenze
poetry install

# 2. Esegui tutti i test
poetry run pytest

# 3. Con coverage
poetry run pytest --cov=vega
```

## 📁 Dove Mettere i Test

```
tests/
├── unit/              👈 Test di singoli componenti (classi, funzioni)
├── functional/        👈 Test di features complete (endpoint, workflow)
└── integration/       👈 Test di più componenti insieme (stack completo)
```

## ✍️ Scrivere un Test

### 1. Test Unitario Semplice

```python
# tests/unit/test_mio_componente.py
import pytest

class TestMioComponente:
    """Test per MioComponente"""

    def test_funzionalita_base(self):
        """Test funzionalità base"""
        # Arrange
        componente = MioComponente()

        # Act
        risultato = componente.fai_qualcosa()

        # Assert
        assert risultato == valore_atteso
```

### 2. Test Web Endpoint

```python
# tests/functional/test_mio_endpoint.py
from starlette.testclient import TestClient
from vega.web import VegaApp

def test_mio_endpoint():
    """Test endpoint HTTP"""
    app = VegaApp()

    @app.get("/test")
    async def test_route():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

### 3. Test Async

```python
import pytest

@pytest.mark.asyncio
async def test_operazione_async():
    """Test operazione asincrona"""
    risultato = await operazione_async()
    assert risultato is not None
```

### 4. Usare Fixtures

```python
def test_con_container(container):
    """Usa fixture dal conftest.py"""
    # Il container è già disponibile!
    service = container.resolve(MioServizio)
    assert service is not None
```

## 🏃 Eseguire i Test

### Tutti i Test
```bash
pytest
# oppure
make test
```

### Per Categoria
```bash
# Solo unit test
pytest tests/unit
make test-unit

# Solo functional test
pytest tests/functional
make test-functional

# Solo integration test
pytest tests/integration
make test-integration
```

### Test Specifico
```bash
# File specifico
pytest tests/unit/test_router.py

# Classe specifica
pytest tests/unit/test_router.py::TestRouterBasics

# Singolo test
pytest tests/unit/test_router.py::TestRouterBasics::test_router_initialization
```

### Con Output Dettagliato
```bash
# Verbose
pytest -v

# Mostra print()
pytest -s

# Entrambi
pytest -vs
```

### Solo Test che Falliscono
```bash
# Ultimi test falliti
pytest --lf

# Test falliti per primi
pytest --ff
```

## 📊 Coverage

```bash
# Genera report coverage
pytest --cov=vega

# Report HTML
pytest --cov=vega --cov-report=html
open htmlcov/index.html

# Con make
make test-cov
make show-cov
```

## 🏷️ Markers

### Usare Markers
```python
import pytest

@pytest.mark.slow
def test_operazione_lenta():
    """Test che richiede tempo"""
    pass

@pytest.mark.integration
def test_integrazione():
    """Test di integrazione"""
    pass
```

### Filtrare per Marker
```bash
# Solo test web
pytest -m web

# Solo test lenti
pytest -m slow

# Escludi test lenti
pytest -m "not slow"

# Combinazioni
pytest -m "web and functional"
```

## 🔧 Fixtures Disponibili

### Dal conftest.py
- `container` - DI container pulito
- `event_bus` - Event bus pulito
- `vega_app` - Applicazione Vega base
- `async_container` - Container async
- `async_event_bus` - Event bus async

### Esempio
```python
def test_con_fixtures(container, event_bus):
    """Usa fixtures multiple"""
    # Setup automatico!
    service = container.resolve(MyService)
    # ... test ...
```

## 🐛 Debug

### Con PDB
```bash
# Entra in debugger su failure
pytest --pdb

# Entra in debugger subito
pytest --trace
```

### Verbose Traceback
```bash
# Traceback completo
pytest --tb=long

# Traceback corto
pytest --tb=short

# Solo l'errore
pytest --tb=line
```

## 📝 Parametrizzazione

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_raddoppia(input, expected):
    """Test con parametri multipli"""
    assert input * 2 == expected
```

## ✅ Checklist Test

Prima di committare:
```bash
# 1. Tutti i test passano
pytest

# 2. Coverage accettabile
pytest --cov=vega --cov-report=term-missing

# 3. Lint OK (opzionale)
make lint

# 4. Format OK (opzionale)
make format
```

## 📚 Risorse

- [README Completo](README.md) - Guida dettagliata
- [TESTING.md](../TESTING.md) - Documentazione completa
- [Pytest Docs](https://docs.pytest.org/) - Documentazione ufficiale

## 🆘 Problemi Comuni

### Import Error
```bash
# Assicurati che vega sia installato
poetry install
```

### Test Async Non Funzionano
```bash
# Verifica pytest-asyncio
poetry add --group dev pytest-asyncio
```

### Coverage Non Funziona
```bash
# Installa pytest-cov
poetry add --group dev pytest-cov
```

## 🎯 Quick Commands

```bash
# Setup
poetry install

# Test veloci (escludi slow)
pytest -m "not slow"

# Test con coverage
make test-cov

# Solo test web
make test-web

# Pulisci artefatti
make clean

# Mostra comandi disponibili
make help
```

---

**Inizia subito:** `poetry run pytest -v` 🚀
