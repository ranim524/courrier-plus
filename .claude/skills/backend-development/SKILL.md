---
name: backend-development
description: FastAPI backend conventions for Courrier+ (routes, services, repositories, schemas)
---

# Backend Development

## Purpose
Keep the FastAPI backend modular, testable, and consistent as new endpoints are added.

## When to use it
Any time you touch `backend/app/`.

## Project conventions
- Layering: `routes` → `services` → `repositories` → `models`. Never skip a layer.
- One router per resource in `app/routes/` (e.g. `letters.py`, `payments.py`, `tracking.py`, `admin.py`, `delivery.py`), all mounted in `app/main.py` with an `/api` prefix.
- Pydantic schemas live in `app/schemas/`, named `<Resource>Create`, `<Resource>Read`, `<Resource>Update`.
- Services return plain data (ORM objects or dicts), never raise `HTTPException` directly — they raise domain exceptions (`app/core/exceptions.py`) which routes translate to HTTP responses via a shared exception handler.
- Repositories take a `Session` and do CRUD only — no business rules.
- Use dependency injection (`Depends`) for DB session, current admin, pagination params.
- Config via `app/core/config.py` using `pydantic-settings`, reading from `.env`. Never read `os.environ` directly elsewhere.

## Important rules
- Do not put logic in `main.py` beyond app creation, middleware, and router includes.
- Every public endpoint validates input via a Pydantic schema — never trust raw `request.json()`.
- Every mutating endpoint that changes letter status must go through the state-machine service (`app/services/letter_state.py`) — never set `.status` directly on the model elsewhere.
- Consistent error shape: `{"detail": "..."}"`. Use the global exception handlers in `app/core/errors.py`.
- Return proper status codes: 201 for creation, 404 for not found, 409 for conflicting state, 422 for validation (FastAPI default), 401/403 for auth.

## Workflow
1. Define/extend Pydantic schema.
2. Add/extend repository method.
3. Add/extend service function (business rules, calls repository + other services like email/payment).
4. Add/extend route calling the service.
5. Add OpenAPI docstring/summary on the route.
6. Write a test in `backend/tests/`.

## Example: adding an endpoint
```python
# routes/letters.py
@router.post("", response_model=LetterRead, status_code=201)
def create_letter(payload: LetterCreate, db: Session = Depends(get_db)):
    return letter_service.create_letter(db, payload)
```
Business rules (reference generation, initial status) live in `services/letter_service.py`, not in the route.
