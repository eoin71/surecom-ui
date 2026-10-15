# surecom-ui

Shared design system and base templates for Surecom's internal Django apps
(SurecomDB / Site Manager and RAMS Generator), so both present one product.

Built on **Tailwind v4**, which configures itself in CSS rather than JavaScript —
that's what makes the design tokens shareable from inside a Python package
without a `node_modules` resolution problem.

---

## Install

Add to each app's `requirements.txt`:

```
surecom-ui @ git+https://github.com/eoin71/surecom-ui@v0.1.0
```

Pin a tag, not a branch, so the two apps can be upgraded independently.

---

## Configure

In each app's `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "surecom_ui",
]

TEMPLATES = [{
    ...
    "OPTIONS": {
        "context_processors": [
            ...
            "surecom_ui.context_processors.ui",
        ],
    },
}]

# ── Shared UI ────────────────────────────────────────────────────────────
SURECOM_UI_APP_NAME = "Site Manager"      # shown in the nav and footer
SURECOM_UI_CURRENT_APP = "sites"          # which entry in SURECOM_UI_APPS is "us"
SURECOM_UI_BETA = True                    # renders the BETA badge

SURECOM_UI_APPS = [
    {"id": "sites", "name": "Site Manager",   "url": "https://sites.surecom.ie", "icon": "map"},
    {"id": "rams",  "name": "RAMS Generator", "url": "https://rams.surecom.ie",  "icon": "document-text"},
]
```

The app switcher shows every entry except `SURECOM_UI_CURRENT_APP`, so both apps
can share the identical `SURECOM_UI_APPS` list.

---

## Build the stylesheet

Tailwind only emits the utility classes it finds in scanned files, so a shared
package can't ship a useful pre-compiled stylesheet — it doesn't know what the
consuming app's templates use. Each app therefore compiles its own, scanning
both its templates and this package's:

```bash
python -m surecom_ui.build --out static/css/app.css --source templates --source . --minify
```

Pass `--source` once per directory to scan. Repeat it for app-level template
dirs (`--source sites`). Add `--watch` during development.

`--print-input` dumps the generated Tailwind entrypoint without building, which
is useful when a class isn't being emitted and you want to check the scan paths.

### Requires the Tailwind CLI

The standalone binary needs no Node. Download it from
[the Tailwind releases page](https://github.com/tailwindlabs/tailwindcss/releases)
and either put it on `PATH` as `tailwindcss` or set `TAILWIND_BIN=/path/to/binary`.

### In a Dockerfile

Run the build before `collectstatic`. It deliberately avoids importing Django,
so it works at image-build time before any environment variables exist:

```dockerfile
ARG TAILWIND_VERSION=v4.1.14
RUN curl -sSLo /usr/local/bin/tailwindcss \
      https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-x64 \
    && chmod +x /usr/local/bin/tailwindcss

RUN python -m surecom_ui.build --out static/css/app.css \
      --source templates --source . --minify
```

---

## Use the base template

```django
{% extends "surecom_ui/base.html" %}
{% load surecom_ui %}

{% block title %}Sites · Site Manager{% endblock %}
{% block brand_url %}{% url 'site_list' %}{% endblock %}

{% block nav_items %}
    {% nav_item "/" "Sites" icon_name="map" %}
    {% if user.is_staff %}
        {% nav_item "/create/" "Add New" icon_name="plus" %}
        {% nav_item "/changes/" "Change Log" %}
    {% endif %}
{% endblock %}

{% block content %}
    <h1>...</h1>
{% endblock %}
```

### Blocks

| Block | Purpose |
|---|---|
| `title` | `<title>` contents |
| `ui_stylesheet` | Override if the compiled CSS isn't at `static/css/app.css` |
| `extra_css` / `extra_js` | Per-page assets |
| `body_class` | Extra classes on `<body>` |
| `nav` | Replace the whole nav |
| `brand_url` | Where the brand link points |
| `nav_items` | App-specific nav links |
| `nav_user_items` | Extra entries in the user dropdown |
| `logout_form` | Override if not using Django's `logout` URL (allauth needs this) |
| `nav_anonymous` | Shown instead of the user menu when logged out |
| `messages` | Replace message rendering |
| `main_wrapper` | Replace the centred container — use for full-bleed layouts |
| `content` | Page content (inside the default wrapper) |
| `footer` | Replace the footer |

**allauth apps** (RAMS) must override `logout_form`, since the default points at
Django's built-in `logout` URL:

```django
{% block logout_form %}
    <a href="{% url 'account_logout' %}" class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
        Sign out
    </a>
{% endblock %}
```

### Full-bleed pages

For a page that manages its own height (the split map/table view):

```django
{% block main_wrapper %}
    <div class="su-split">
        <div class="su-split-map">{# map #}</div>
        <div class="su-split-panel">{# table #}</div>
    </div>
{% endblock %}
```

---

## Components

CSS classes, all prefixed `su-`:

- **Buttons** — `su-btn-primary`, `su-btn-secondary`, `su-btn-danger`, `su-btn-ghost`
- **Cards** — `su-card`, `su-card-header`, `su-card-body`, `su-card-footer`
- **Badges** — `su-badge-neutral|brand|warning|success|danger`
- **Tables** — `su-table` (sticky header), `su-row-highlight`
- **Forms** — `su-label`, `su-input`, `su-help`, `su-error`
- **Alerts** — `su-alert-info|success|warning|error`
- **Nav** — `su-nav`, `su-nav-link`, `su-nav-link-active`
- **Split layout** — `su-split`, `su-split-map`, `su-split-panel`, `su-split-panel-header|body|footer`

Template partials:

```django
{% include "surecom_ui/components/page_header.html" with title="Sites" subtitle="1,284 records" %}
{% include "surecom_ui/components/empty_state.html" with title="No results" icon_name="magnifying-glass" %}
{% include "surecom_ui/components/field.html" with field=form.name %}
```

---

## Icons

`{% icon "name" %}` inlines an SVG from `surecom_ui/icons/`:

```django
{% icon "plus" %}
{% icon "magnifying-glass" css_class="size-5 text-gray-400" %}
{% icon "x-mark" label="Close" %}       {# labelled instead of aria-hidden #}
```

**To add an icon:** download the 24×24 *outline* SVG from
[heroicons.com](https://heroicons.com) and save it to `surecom_ui/icons/<name>.svg`.
No code change needed — the tag loads by filename and caches.

An unknown name renders an HTML comment instead of raising, so a typo can't
take a page down.

The seed set is deliberately small (`x-mark`, `plus`, `chevron-down`,
`chevron-right`, `check`, `magnifying-glass`). RAMS leans on icons heavily, so
expect to add a batch during its migration — `map`, `document-text`,
`user-circle`, `cog-6-tooth`, `shield-check`, `trash`, `pencil-square`,
`exclamation-triangle`.

---

## Versioning

Tag releases (`v0.1.0`) and bump the pin in each app deliberately. Because the
two apps migrate on different schedules, never point either at a moving branch.
