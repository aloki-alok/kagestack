---
name: python
description: Rules for writing Python that a type checker can check. Use when writing or editing .py files.
paths: ["**/*.py", "**/*.pyi"]
---

# Python

Make the type checker reject bad states, so a reader trusts the types instead of re-checking values.

| Rule | How |
|---|---|
| Signatures are typed | Every parameter and return of a function you write or change. `-> None` too. |
| Outside data is parsed where it enters | Requests, webhooks, env, config, JSON and DB rows become a frozen `dataclass`, a pydantic model or a `TypedDict` at the boundary. Inside, pass the type, not a `dict`. |
| `Any` stops at the boundary | The parse function may take `Any` or `object`. Nothing after it returns `Any`. |
| States are enums or literals | `Literal['queued', 'sent']` or an `Enum`, not loose strings. End a `match` on them with `case _: assert_never(value)`. |
| Ids can't be swapped | `OrderId = NewType('OrderId', str)` when two ids share a type. |
| Catch the error you expect | Never a bare `except:` or `except Exception: pass`, which `ks check` sends back. Re-raise with `raise ... from error` when you translate one. |
| No mutable defaults | `items: list[str] | None = None`, then build the list inside. |
| Seams are protocols | A `Protocol` for what a test double must provide, not a base class. |
| Paths and logs | `pathlib.Path`, not `os.path`. `logging` with the ids that matter, not `print`, in library code. |
| Suppressions name the rule | `# type: ignore[attr-defined]`, never a bare `# type: ignore`, which `ks check` sends back. |
| When the framework types badly | Odoo models and similar ORMs: type the plain functions around them and leave the ORM calls alone. |

Before you finish, run the repo's type checker (`ty check`, `mypy` or `pyright`, whichever its config names) and `ruff check` on the files you changed. With no config, use `uvx ruff check --select E,F,B,I <files>` and ignore hits on lines you didn't touch.
