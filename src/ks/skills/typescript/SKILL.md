---
name: typescript
description: Rules for writing TypeScript that the compiler can check. Use when writing or editing .ts or .tsx files.
paths: ["**/*.ts", "**/*.tsx", "**/*.mts", "**/*.cts"]
---

# TypeScript

Make the compiler reject bad states, so a reader trusts the types instead of re-checking values.

| Rule | How |
|---|---|
| Outside data is `unknown` until parsed | Requests, responses, JSON, env, storage and query params enter as `unknown`. Parse them where they enter with the repo's schema library, and take the type from the schema (`z.infer<typeof Order>`). |
| No `any` | `ks check` sends back a new one. Use `unknown` and narrow it. |
| Casts only after a check | `as` hides bugs. Narrow with a discriminant, `in`, `typeof` or a type guard that really checks. A guard that lies is worse than `as`. Use `satisfies` to check a literal without widening it. |
| States are unions | Give each variant a literal `kind` or `status`. No bag of optional fields where some combinations are impossible. |
| Every variant handled | End a `switch` on a union with `const unhandled: never = value`, so a new variant fails the build. |
| Ids can't be swapped | Two `string` ids that mean different things get brands (`string & { readonly brand: 'OrderId' }`), made only by a parse or guard. |
| Derive before declaring | `Pick`, `Omit`, `ReturnType`, `Awaited`, `typeof` and schema types before a new interface that drifts. |
| No `!` | Narrow instead. A non-null assertion is a cast. |
| Object arguments | Three or more parameters, or any boolean flag, go in one object, so a call reads like what it means. |
| Errors reach someone | Catch only the error you expect. `ks check` sends back an empty `catch` or `.catch(() => {})`. Give a deliberate ignore a named handler. |
| Suppressions name the rule | `@ts-expect-error` over `@ts-ignore`, which `ks check` sends back. Fix the type first. |

Before you finish, run the repo's type check (`tsc --noEmit` or its `typecheck` script) and its linter on the files you changed.
