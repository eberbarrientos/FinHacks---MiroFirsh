# Test Suite

## Running Tests

### Schema Tests (No Database Required)
```bash
python3 -m pytest tests/test_schemas.py -v
```

### Model and API Tests (Require PostgreSQL)
The model and API integration tests require PostgreSQL due to UUID type usage.

**Option 1: Run with Docker**
```bash
docker-compose up -d postgres
python3 -m pytest tests/test_models.py tests/test_api_portfolios.py -v
```

**Option 2: Skip Database Tests**
```bash
python3 -m pytest tests/test_schemas.py -v
```

## Test Coverage

- `test_schemas.py`: Pydantic schema validation (12 tests) ✅
- `test_models.py`: Database model tests (8 tests) - Requires PostgreSQL
- `test_api_portfolios.py`: API endpoint tests (15 tests) - Requires PostgreSQL

## Notes

- Schema tests use no database and run quickly
- Model/API tests require PostgreSQL with UUID support
- SQLite cannot be used for model tests due to UUID type incompatibility
