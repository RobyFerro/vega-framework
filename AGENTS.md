# Guida per agenti Vega

Documento operativo da pubblicare in ogni nuovo progetto creato con `vega init`. Riassume l’architettura, le regole di collaborazione e i comandi CLI ufficiali che un agente deve conoscere. Mantieni il codice entro i limiti della Clean Architecture indicata di seguito.

## Architettura base
- 4 layer obbligatori: `domain` (logica di business pura), `application` (workflow/mediator), `infrastructure` (implementazioni tecnologiche), `presentation` (CLI/Web, solo I/O e validazione).
- Regola delle dipendenze: Presentation → Application → Domain ← Infrastructure. Il dominio non dipende da nessuno.
- File chiave generati da `vega init`: `config.py` (container DI, mappa interfacce→implementazioni), `settings.py` (configurazione Pydantic), `main.py` (entry point), `events/__init__.py` (auto-registrazione handler), eventuale scaffold web sotto `presentation/web/`.

## Struttura di progetto
```
domain/ {entities, repositories, services, interactors, events}
application/ mediators/
infrastructure/ {repositories, services, models?}
presentation/ {cli/commands, web/{routes,middleware,models}?}
tests/ per layer
```

## Convenzioni dominio (contesti, aggregate, VO)
- Il framework non ha generator dedicati per bounded context, aggregate o value object: crea classi Python pure sotto `domain/` rispettando la separazione per layer.
- Puoi isolare un contesto creando sottocartelle coerenti (es. `domain/billing/entities/...`) mantenendo la stessa suddivisione `entities/repositories/services/interactors`.
- Value Object: dataclass/enum immutabili o con validazioni locali in `domain/entities`. Nessun riferimento a infrastruttura/framework.
- Aggregate: incapsula invarianti nell’aggregate root in `domain/entities`; esponi operazioni tramite interactor singolo per caso d’uso.

## Comandi ufficiali (eseguili dal root del progetto)
- Inizializzazione progetto: `vega init <nome> [--template basic|web|fastapi|ai-rag] [--path PATH]`
- Aggiunte opzionali:
  - Web: `vega add web`
  - SQLAlchemy: `vega add sqlalchemy`
- Generazione componenti (`vega generate <tipo> <Nome> [opzioni]`):
  - `entity` → `domain/entities/`
  - `repository|repo` → `domain/repositories/` (+ `--impl <nome>` per `infrastructure/repositories/`)
  - `service` → `domain/services/` (+ `--impl <nome>` per `infrastructure/services/`)
  - `interactor` → `domain/interactors/`
  - `mediator` → `application/mediators/`
  - `event` → `domain/events/` (dataclass immutabile)
  - `event-handler|subscriber` → `events/` (ricorda di chiamare `events.register_all_handlers()` in bootstrap)
  - `model` → `infrastructure/models/` (richiede `vega add sqlalchemy`)
  - `router` → `presentation/web/routes/` (richiede `vega add web`)
  - `middleware` → `presentation/web/middleware/` (per-route, richiede `vega add web`)
  - `webmodel` → `presentation/web/models/` con flag obbligatori `--request` o `--response` (richiede `vega add web`)
  - `command` → `presentation/cli/commands/` (`--impl sync` per comando sincrono)

## Regole di implementazione per agenti
- Inserisci la logica di business solo nel dominio (interactor/metodi di entity); niente SQL/HTTP/framework nel dominio.
- Orchestrazione multi-passaggio? Usa un `Mediator` nell’application e delega ai singoli `Interactor`.
- Implementazioni concrete (DB, API esterne) solo in `infrastructure` e bind in `config.py`.
- Presentation gestisce input/output e mapping verso gli interactor, senza logica di business.
- Eventi: definisci l’evento in `domain/events/`, gli handler in `events/`, registra tutti con `events.register_all_handlers()`.
- Web: middleware generati sono per-route (`@middleware(...)`); per middleware di applicazione usa Starlette `BaseHTTPMiddleware`.

## Note operative
- Esegui i generator dal root dove risiedono `config.py` e `pyproject.toml` (o passa `--path`).
- Non inventare nomi o struttura: attenersi ai comandi sopra; per concetti non coperti dal CLI (aggregate/VO/contesti) creare manualmente nel dominio seguendo le regole di purezza e separazione.
