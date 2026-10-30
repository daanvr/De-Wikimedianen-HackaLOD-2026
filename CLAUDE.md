# Instructies voor code agents
Deze repo is de code-repo van **De Siboga Expeditie**, de website van team De Wikimedianen voor de HackaLOD 2026. Op dit moment werken Daan en Hay eraan.

## Project in het kort
- De website is statisch: een Vue 3-frontend (JavaScript, geen TypeScript) met SCSS.
- De frontend leest één JSON-bestand plus losse bestanden (plaatjes, later misschien audio). Dat heet de **frontend data**.
- De frontend data wordt gemaakt door een Python-pipeline. Die leest de content-repo (Obsidian-markdown met YAML-frontmatter), haalt de Linked Data-bronnen op waar de frontmatter naar verwijst, cachet die in SQLite, en voegt alles samen.
- De content-repo ([hay/siboga-content](https://github.com/hay/siboga-content)) is de *source of truth* en wordt alleen gelezen. Alle techniek staat in deze repo.
- Het is een hackathon: houd het eenvoudig, maar modulair. Er wordt later veel op voortgebouwd.

## Documentatie eerst
De documentatie in [docs/](docs/README.md) beschrijft hoe het systeem in elkaar zit. Lees die voordat je iets bouwt. Wijkt de code af van de documentatie, pas dan de documentatie aan in dezelfde wijziging, of vraag eerst welke van de twee klopt.

Werk per taak: maak voor een concrete taak eerst een plan en bouw dan pas.

## Markdown: GitHub hier, Obsidian in de content-repo
De twee repo's worden op een andere manier gelezen, en de markdown volgt dat.
- **Deze repo** lezen we vooral in de browser, op GitHub. Schrijf GitHub-markdown: gewone links met relatieve paden (`[pipeline](docs/pipeline.md)`), tabellen, codeblokken en Mermaid-diagrammen. Geen Obsidian-wikilinks, want GitHub maakt daar geen link van.
- **De content-repo** lezen en schrijven we in Obsidian. Daar zijn wikilinks (`[[Anna Weber]]`), embeds (`![[foto.jpg]]`) en andere Obsidian-schrijfwijzen gewoon. De pipeline moet die begrijpen; zie [docs/content-repo.md](docs/content-repo.md).

## Frontend: aanvullende instructies
<!-- PLACEHOLDER: hier komen nog instructies van Daan over de frontend (uit zijn eigen Claude-specificaties). Tot die er staan: volg docs/frontend.md en de codeconventies hieronder. -->

## Pipeline: aanvullende instructies
<!-- PLACEHOLDER: hier komen nog instructies van Daan over wat de Python-pipeline wel en niet moet doen. Tot die er staan: volg docs/pipeline.md en de codeconventies hieronder. -->

# Code agent instructions
## General
- Use 4 spaces for indentation
- Clear variable/function names
- NEVER have a trailing newline at the end of files, so that the very last line of a file is a newline.
- Use exactly ONE empty line between sections of code (functions, classes, blocks), NEVER two consecutive empty lines (so not PEP 8 style double blank lines between top-level definitions)
- Put methods in classes in alphabetical order

## Markdown
- **No blank line after headings** — text starts on the very next line after a `#` heading

## Shell
- The shell is `zsh`. Unmatched globs are a fatal error, not passed through literally — an unquoted `--include=*.py` aborts the command with `no matches found` before the tool runs. Always quote glob patterns meant for the tool, not the shell: `grep -rn "x" --include="*.py"`, `find -name "*.toml"`. Same for any arg with `*`, `?`, or `[...]`.
- There is no `timeout` on the PATH. To bound a process: background it, `sleep`, then `kill $!`.

## JavaScript
- **Always use semicolons**
- camelCase for variables/functions, PascalCase for classes
- Use `const` by default, `let` when needed
- **Spaces around colons in object literals**: `{ key : value }`
- Arrow function parameters always use parentheses: `(item) =>` not `item =>`
- Regular `function` declarations for named/top-level functions; arrow functions for callbacks, `.map()`/`.filter()`, and one-liner computed values
- ES modules: default exports for classes, named exports for utility functions and constants
- When using objects ALWAYS put every key/value pair on a newline, so not this:
```js
foo = { bar : 1, baz : 2 }
```
But this:
```js
foo = {
    bar : 1,
    baz : 2
}
```

### Special rules for Vue.js
- **Composition API with `<script setup>` exclusively** — no Options API in components
- SFC block order: `<script setup>`, then `<template>`, then `<style>`
- File naming: kebab-case with prefixes — `el-*.vue` for components, `vw-*.vue` for views
- Use components in templates with kebab-case: `<el-button>`, `<el-slider>`
- Use verbose directive syntax: `v-bind:` and `v-on:` (not `:` and `@` shorthands)
- Props via `defineProps()` with runtime type objects; emits via `defineEmits()`
- Use `ref()` and `computed()` for reactivity — no `reactive()`
- Use `provide`/`inject` for shared context (store, i18n, router) rather than importing the store directly in every component
- Toggle custom HTML attributes with `v-bind:attr="condition ? '' : null"` as CSS hooks (e.g. `is-visible`, `is-current`, `has-placeholder`)
- Script setup ordering: imports, inject, defineEmits/defineProps, ref/computed, functions, lifecycle hooks, defineExpose
- Always put Vue attributes in HTML on newlines, so:
```html
<el-component
    v-bind:foo="bar"
    v-on:click="baz()" />
```

#### Vue.js and SASS
- Look in this document under 'CSS / SASS' rules for more, these apply specifically for Vue.js
- `<style lang="scss" scoped>` on all component style blocks
- Use scoped styles, simpler class names are fine (`.content`, `.text`)
- `:deep()` for piercing scoped styles into child components
- Root element class matches component name: `.el-button`, `.vw-story`

### Example
```javascript
function calculateTotal(items) {
    const total = items.reduce((sum, item) => sum + item.price, 0);
    return total;
}

class UserManager {
    async fetchUser(id) {
        const response = await fetch(`/api/users/${id}`);
        return response.json();
    }
}
```

## PHP
- camelCase for variables/functions, PascalCase for classes
- Always use type hints
- `declare(strict_types=1);` at the top
### Example
```php
<?php
declare(strict_types=1);

function calculateDiscount(float $price, float $percentage): float {
    return $price * ($percentage / 100);
}

class ProductRepository {
    public function __construct(private PDO $db) {}

    public function findById(int $id): ?Product {
        $stmt = $this->db->prepare('SELECT * FROM products WHERE id = ?');
        $stmt->execute([$id]);
        return $stmt->fetchObject(Product::class) ?: null;
    }
}
```

## Python
### General remarks
- snake_case for variables/functions, PascalCase for classes
- **Spaces around = in function arguments**: `def foo(bar = 1):`
- Multi-line function definitions on separate lines
- Put imports in alphabetical order
- Also put methods in classes in alphabetical order

### Other preferences
* Use [[Dataclasses]]
* Use [[Pydantic]]
* Use [[Logging (Python)]] with [[Loguru]]
* Use [[Python enums]]
* Use configuration files in [[TOML]]. Use a `defaults.toml` file that can be checked in while also providing a `config.toml` file that overwrites the values in that file.
* Use [[Pytest]] to write unit tests instead of [[Python unittest]]
* Use [[uv]] with a `pyproject.toml` for dependencies and virtual environments — never `requirements.txt` or plain `pip`/`venv`

### Example
```python
def calculate_average(
    numbers: list[float],
    exclude_zeros: bool = False
) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

class DataProcessor:
    def __init__(self, config: dict):
        self.config = config

    def process_data(self, data: list) -> dict:
        return {self._key(item): self._transform(item) for item in data}
```

## SCSS / CSS / SASS
- When using SASS always use SCSS syntax (curly braces, not indented Sass)
- Use `@use` exclusively — never `@import`
- **CSS custom properties** for all design tokens (colors, font sizes, spacing) — not SCSS variables (except for breakpoint values)
- BEM-like modifiers with `--`: `.el-button--fit`, `.block--chapter`
- **Custom HTML attributes as style hooks** with attribute selectors: `&[is-visible]`, `[flair="icon"]`, `[data-type="item"]`
- Use `&` parent selector for BEM nesting, pseudo-elements, hover/focus states, and attribute selectors
- `rem` as the primary unit; `px` only for borders, shadows, and small fixed-size elements
- Keep nesting to 2-3 levels maximum
