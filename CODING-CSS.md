# CSS Style Guide Instructions for LLM

When writing CSS, SCSS, or any styling code, follow these rules.

## Naming Convention: BEM

Use the BEM (Block, Element, Modifier) methodology for all class names:

- **Block**: standalone component (`.card`, `.menu`, `.button`)
- **Element**: part of a block, separated by `__` (`.card__title`, `.menu__item`)
- **Modifier**: variant or state, separated by `--` (`.button--primary`, `.card--featured`)

### Example

```css
.card { }
.card__header { }
.card__title { }
.card__title--large { }
.card--featured { }
```

Avoid deep nesting like `.card__header__title__icon`. Keep it to one element level: `.card__header-icon`.

## Preprocessor: SCSS

Use SCSS (Sass) syntax. Prefer:

- Variables for colors, spacing, breakpoints (`$primary-color`, `$spacing-md`)
- Mixins for reusable patterns (media queries, flex centering)
- Nesting for BEM structure using the `&` parent selector
- Avoid nesting more than 3 levels deep

### Example

```scss
.card {
  padding: $spacing-md;

  &__title {
    font-size: $font-lg;

    &--large {
      font-size: $font-xl;
    }
  }

  &--featured {
    border: 2px solid $primary-color;
  }
}
```

## General Rules

1. One component per file, named after the block (`_card.scss`).
2. Use kebab-case for class names (`.user-profile`, not `.userProfile`).
3. No ID selectors for styling. Classes only.
4. Avoid `!important` unless overriding third-party styles.
5. Mobile-first media queries using `min-width`.
6. Use CSS custom properties (`--variable`) for runtime theming, SCSS variables for build-time constants.
7. Group properties logically: positioning, box model, typography, visual, misc.
8. No inline styles unless dynamically computed.

## Output Format

When generating styles, always include a brief comment at the top of each block explaining what the component is, and explain BEM choices if non-obvious.