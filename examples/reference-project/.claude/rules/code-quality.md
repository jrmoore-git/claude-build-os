---
paths:
  - src/**
---

# Code Quality

- No nesting deeper than 3 levels. Use guard clauses and early returns.
- All database queries use parameterized SQL (`?` placeholders). Never interpolate strings into SQL.
- Every public function has a one-line docstring. No multi-paragraph docstrings — if the function needs that much explanation, it's too complex.
- Type hints on all function signatures. No `Any` unless interfacing with untyped external libraries.
