# ControlShift Frontend Design Specification

**Status:** approved design direction (Phase 6A.4), the implementation reference for Phase 6B.
**Scope:** shared application shell, Control Explorer, design tokens, `CrosswalkEntry`, provenance, responsive behavior, accessibility, and loading/empty/error/not-found states. Overview, Ask ControlShift and Compare Frameworks get only consistency rules here (section 14); each will receive its own specification.
**Stack:** Next.js (App Router), React, TypeScript, Tailwind CSS, selectively customized shadcn/ui. The browser talks to a same-origin Next.js proxy that forwards to FastAPI.

Values in this document are initial targets. Layout widths and breakpoints must be validated against rendered screenshots (section 16) before being treated as final.

---

## 1. Product design principles

1. **Authoritative data stands alone.** Official NIST records are browsable without any LLM. Nothing in Explorer depends on generation.
2. **Three kinds of content are always distinguishable.** Every piece of content is one of: *Official NIST text* (verbatim from the PDFs or the transition workbook), *ControlShift-derived interpretation* (labels computed by ControlShift), or *AI-generated explanation* (Ask ControlShift only). Typography, border style and an explicit text label must all agree. Color or style is never the only signal.
3. **Never overstate.** The UI does not claim equivalence between equal-looking IDs across versions, does not describe an absent crosswalk reference as removal, does not choose between conflicting workbook rows, and does not imply capabilities the backend lacks (search is deterministic substring matching, not semantic ranking).
4. **Quiet shell, loud content.** Chrome is low-contrast and hairline-thin. The record's identity, official text, source and crosswalk carry the visual weight.
5. **Dense where scanning, generous where reading.** Lists are compact. Official text is set at a comfortable measure.
6. **Restraint.** No gradients, glows, glassmorphism, decorative charts, fabricated analytics, chat bubbles, or cards-inside-cards. Motion is minimal.

---

## 2. Approved visual identity: "Two inks on paper"

ControlShift is about two official documents and the official record linking them.

- **Paper:** a warm off-white canvas with white working surfaces and hairline borders. No shadows except on overlays.
- **Two inks:** teal marks CSF 2.0 and violet marks CSF 1.1. Version ink is used only for version identity (chips, crosswalk connectors, the version toggle underline, function IDs in the tree), never for decoration or status.
- **Three typefaces, three meanings:**
  - **IBM Plex Sans:** application UI.
  - **IBM Plex Mono:** framework IDs and technical identifiers (control IDs, workbook row numbers, hashes).
  - **Source Serif 4:** verbatim official NIST text and workbook quotations only. Never used for headings, buttons, ControlShift-derived text or generated text.
- **Source labeling:**

| Kind | Label | Border treatment | Type treatment |
|---|---|---|---|
| Official NIST text | black `NIST` tag + location (version, page) | solid 1px | Source Serif 4 |
| ControlShift-derived interpretation | dashed-bordered `Derived` tag | dashed 1px `#B9BCC2` | Plex Sans, `text-2` |
| AI-generated explanation | `AI-generated` tag (Ask page only) | defined in the Ask spec; must be visually distinct from both of the above | Plex Sans |

- **Cobalt** (`accent`) is reserved for links, focus rings and selection. **Amber** and **red** are semantic only (section 3).

---

## 3. Design tokens and typography

### 3.1 Typefaces

| Role | Family | Loading |
|---|---|---|
| UI | IBM Plex Sans | `next/font`, variable or weights 400/500/600 |
| Identifiers | IBM Plex Mono | `next/font`, weights 400/500 |
| Official text | Source Serif 4 | `next/font`, optical size axis, weight 400 (+ italic 400 for workbook comments) |

All tokens are CSS variables read by Tailwind. Components must not use raw Tailwind palette colors or ad-hoc hex values.

### 3.2 Type scale

Default UI text is **14px**. Smaller sizes are for dense navigation, identifiers, captions and metadata. Weights are 400, 500 and 600 only. Numbers use `font-variant-numeric: tabular-nums`.

| Token | Size/line-height | Weight | Family | Use |
|---|---|---|---|---|
| `label` | 11/16, +0.04em, uppercase | 500 | Sans | Section eyebrows ("OFFICIAL CROSSWALK"), level label |
| `caption` | 12/16 | 400 | Sans | Metadata, counts, result meta line, provenance values |
| `ui-sm` | 13/20 | 400/500 | Sans | Dense navigator rows, tooltips, chips text, compact controls |
| `ui` | 14/20 | 400/500 | Sans | **Default**: buttons, inputs, notices, labels, body copy in the shell and notices |
| `body` | 14/22 | 400 | Sans | Multi-line explanatory copy (notices, state blocks) |
| `title-sm` | 15/22 | 600 | Sans | Section headings |
| `title` | 18/26 | 600 | Sans | Page title in the shell header |
| `name-lg` | 22/28 | 600 | Sans | Element `name` in the record header (when non-null) |
| `id` | 12/16 | 500 | Mono | IDs in tree/list/search rows |
| `id-lg` | 22/28 | 500 | Mono | Primary ID in the record header |
| `mono-sm` | 12/16 | 400 | Mono | Row numbers, hashes, informative references |
| `source-lg` | 18/28 | 400 | Serif | Official description in the record header |
| `source` | 15/24 | 400 | Serif | Official text in crosswalk entries, children, workbook comments (italic) |

On screens below 900px, `source-lg` becomes 17/26; other tokens are unchanged.

### 3.3 Color (light theme; the variables are structured so a dark theme can be added later)

**Neutrals**

| Token | Hex | Use |
|---|---|---|
| `canvas` | `#F6F6F3` | App background (warm off-white) |
| `surface` | `#FFFFFF` | Working panes |
| `surface-sunken` | `#F1F1ED` | Sidebar, rail, code wells |
| `surface-hover` | `#EEEEE9` | Row hover |
| `surface-pressed` | `#E7E7E1` | Pressed state |
| `border` | `#E3E3DD` | Hairlines |
| `border-strong` | `#CFCFC7` | Input borders |
| `text-1` | `#17191C` | Primary text |
| `text-2` | `#474C55` | Secondary text |
| `text-3` | `#676C75` | Metadata (5.28:1 on white, 4.87 on canvas, 4.66 on surface-sunken, 4.53 on surface-hover) |
| `text-4` | `#9EA2A8` | Placeholders and disabled only; never used for information |

**Interactive**

| Token | Hex | Use |
|---|---|---|
| `accent` | `#2456D3` | Links, focus ring, selection bar |
| `accent-soft` | `#EDF2FD` | Selected-row background |
| `ink` | `#17191C` | Primary button fill (white text), `NIST` tag fill |

**Version inks (identity only)**

| Token | Text/stroke | Soft fill | Border |
|---|---|---|---|
| `v20` (CSF 2.0, teal) | `#0F766E` | `#E8F4F2` | `#B5DCD6` |
| `v11` (CSF 1.1, violet) | `#6B46C1` | `#F2EEFB` | `#D6CCF1` |

**Semantic**

| Token | Text/edge | Soft fill | Use |
|---|---|---|---|
| `notice-ambiguous` | `#A15C07` | `#FDF6EA` | Multiple crosswalk entries requiring interpretation |
| `error` | `#B42318` | `#FEF3F2` | Request/backend failures only |
| `neutral-notice` | `#474C55` | `#F1F1ED` | No crosswalk reference; info |
| `derived` | `#5B616B` | none | Text of `Derived` tag; border `#B9BCC2` dashed |
| `highlight` | n/a | `#FFF1C2` | Search match highlight background |

Absence of a crosswalk reference uses `neutral-notice`, never `error` or `notice-ambiguous`.

### 3.4 Borders, radius, spacing, elevation

- **Borders:** 1px `border` for panes and dividers. Panes are divided by hairlines, not gaps. Inputs use `border-strong`. Dashed 1px `#B9BCC2` is reserved for derived content.
- **Radius:** `r-sm` 4px (chips, ID tags), `r-md` 6px (inputs, buttons, rows), `r-lg` 8px (notices, popovers, the crosswalk list), `r-xl` 12px (mobile sheets only). Pill radius is used only on the version toggle and the derived summary chip.
- **Spacing:** 4px base; steps 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48. Row padding 8×12; section gap 32; pane gutters 24 (desktop) / 16 (below 900px).
- **Elevation:** none on panes. Popovers, sheets and tooltips use `0 8px 24px rgba(23,25,28,.10), 0 0 0 1px #E3E3DD`.

### 3.5 Iconography

Lucide, 16px, 1.5px stroke, `text-3` (or `text-1` when active). 14px inside chips, 18px in the mobile top bar. Icons support labels and never replace them, except in the collapsed sidebar where tooltips supply names. One icon per concept:

| Concept | Icon |
|---|---|
| Overview | `layout-grid` |
| Ask ControlShift | `message-square-text` |
| Control Explorer | `library` |
| Compare Frameworks | `git-compare-arrows` |
| Official source | `file-text` |
| Crosswalk | `arrow-right-left` |
| Multiple entries | `split` |
| No crosswalk reference | `circle-dashed` |

### 3.6 States

| State | Treatment |
|---|---|
| Hover | Row background `surface-hover`; links underline (1px, offset 3px); no motion |
| Focus | `:focus-visible` only; 2px `accent` outline with 2px offset; never removed |
| Selected | `accent-soft` background, 2px inset left bar in `accent`, text weight 500 |
| Active nav | `surface` fill on the sunken sidebar, `text-1` icon and label |
| Pressed | `surface-pressed` |
| Disabled | `text-4`, no hover, `cursor: not-allowed`, a tooltip stating why |

Transitions: 120ms on color/background only; 160ms for expand/collapse height. Both are disabled under `prefers-reduced-motion`. There are no page transitions.

### 3.7 Density and whitespace

- Navigator rows: 32px (tree), 52px (search results, two lines). Below 900px, tap targets are at least 44px.
- Reading content (official text) is set at a measure of **680–720px** maximum where width permits.
- No region has more than 96px of unexplained empty space. No hero sections inside working pages.
- At most one level of bordered container inside a pane.
- shadcn defaults (ring, shadow, size) are visibly overridden to these tokens, with one size per control: buttons 32px (28px compact), inputs 36px (40px on mobile).

---

## 4. Shared application shell

```
┌──────────────┬───────────────────────────────────────────────────────────┐
│ ◧ ControlShift│  Control Explorer                    [CSF 2.0 | CSF 1.1] │ 56px
│              ├───────────────────────────────────────────────────────────┤
│ Overview     │                                                           │
│ Ask          │                      page workspace                       │
│ Explorer     │                                                           │
│ Compare      │                                                           │
│ ──────────── │                                                           │
│ ● API online │                                                           │
└──────────────┴───────────────────────────────────────────────────────────┘
   232px            (56px when collapsed)
```

**Sidebar** (`surface-sunken`, 1px right border):
- Width 232px expanded, 56px collapsed.
- Brand row 56px: a 20px mark (two offset squares, one teal and one violet, joined by one stroke), followed by the wordmark "ControlShift" (Sans 600, 15px).
- Navigation items, in this order: Overview, Ask ControlShift, Control Explorer, Compare Frameworks. Each is 32px tall with 6px radius, a 16px icon and a 13px/500 label (`ui-sm`; 14px truncates "Compare Frameworks" beside its tag at 232px), 8px horizontal inset.
- Compare Frameworks carries a `caption` tag "Soon" until implemented, and opens a truthful placeholder page. It is not rendered as disabled.
- **Footer status** is driven by `GET /health` and shows only fields that endpoint returns:
  - A status dot plus "API online" when the request succeeds, or "API unreachable" in `error` when it fails.
  - "LLM not configured" when `llm.configured` is false.
  - Activating it opens a popover with `database.chunks`, `database.elements`, `database.crosswalk_rows`, `retrieval.mode` and, when configured, `llm.provider` and `llm.model`. Never display secrets (the endpoint returns none).
- **Collapse:** a toggle at the bottom of the sidebar (a chevron cannot share the brand row with the 56px rail) toggles expanded/collapsed at 1200px and wider. The choice is remembered per browser and is applied before first paint (an inline script sets `data-sidebar` on `<html>`), so the sidebar never shows the wrong width on load. Collapsed items show tooltips. Nav link accessible names always come from their visible text (labels are visually hidden, not removed, in the rail), so a status tag such as "Soon" stays part of the name. A keyboard shortcut for this is a deferred enhancement (section 17).

**Page header:** 56px tall, `surface`, bottom hairline. Left: page title (`title`). Right: page-scoped controls (on Explorer, the version toggle). No subtitle paragraph.

**Workspace:** panes fill the remaining space edge to edge, divided by hairlines. Reading pages (Overview) center content on `canvas` at a maximum width of 1080px.

**Mobile and narrow (<900px):** a 52px top bar contains the menu button, page title and one contextual action. The menu opens a left sheet with the same navigation and status footer. There is no bottom tab bar. The sheet traps focus, closes on `Escape` and on selection, and returns focus to the menu button.

---

## 5. Responsive layout rules

These are the only layout breakpoint rules. They apply to the shell and to Explorer.

| Viewport width | Sidebar | Navigator | Record | Facts rail | Source details |
|---|---|---|---|---|---|
| **≥1640px** | Expanded (232) | Hierarchical, 340 | Reading pane, fluid, content ≤720 | **Permanent**, 264 | Disclosure in the rail |
| **1200–1639px** | Expanded (232) | 340 (320 at ≤1319px) | Spacious pane, content ≤720 | None | Inline disclosure in the record header |
| **900–1199px** | **Collapsed (56)**; click expands it as an overlay that does not push content | Narrower, 288 | Fluid, content ≤720 | None | Inline disclosure (on demand) |
| **<900px** | Hidden; menu sheet | Separate view | Separate view | None | Inline disclosure |

Rules:
1. Prioritize readable content over preserving extra columns. The facts rail exists only where the record pane keeps a comfortable reading width (≥1640px).
2. Below 900px, results and record detail are separate screens (section 8.6). Touch targets ≥44px.
3. No horizontal page scroll at any width. Long IDs and hashes truncate in the middle with a way to reveal the full value. Section paths wrap.
4. Panes scroll independently on desktop. Below 900px the page is a single document scroll.
5. Sticky regions: desktop, the navigator header and the facts rail; below 900px, the top bar and the search field.
6. These widths are initial targets and must be validated against screenshots at 1920, 1640, 1440, 1280, 1200, 1024, 900, 768 and 390px (section 16). If a measured layout fails the criteria, adjust the breakpoint rather than the content.

---

## 6. Control Explorer information architecture

**Evaluation of master-detail:** retained, with refinements. A hierarchical navigator beside a reading pane matches how NIST frameworks are structured and read (browse the hierarchy, read one record, follow its relationships). Flat tables or card grids would hide the hierarchy. The refinements are: a tree in browse mode that becomes a flat result list in search mode, a record pane with a limited reading measure, and a supplementary facts rail only at wide widths.

**Routes**

| Route | Meaning |
|---|---|
| `/explorer` | Browse. Query parameters carry navigator state: `v` (1.1 or 2.0, default 2.0), `level`, `fn` (function), `cat` (category), `q` (search text). |
| `/explorer/{version}/{element_id}` | A record. The version is in the path. The same optional navigator-context parameters (`level`, `fn`, `cat`, `q`) may follow as the query string, so the navigator keeps its state while a record is open. |

Examples: `/explorer?v=2.0`, `/explorer?v=2.0&q=supply`, `/explorer/2.0/GV.SC-03?q=supply`, `/explorer/1.1/PR.AT-01`.

Information priority within a record: (1) identity and version, (2) official text with its source, (3) official crosswalk, (4) children, (5) informative references, (6) source details.

---

## 7. Explorer screen regions and dimensions

```
≥1640px
┌ sidebar ┬─ Navigator 340 ─────────┬─ Record (content ≤720) ─────────────┬─ Facts rail 264 ─┐
│ 232     │ [⌕ Search ID or text  /]│ CSF 2.0 › Govern › Supply Chain…    │ RECORD           │
│         │ [Level ▾] [Function ▾]  │ [2.0] SUBCATEGORY                   │ Version  2.0     │
│         │ 106 elements · CSF 2.0  │ GV.SC-03                    ⧉       │ Level    Subcat. │
│         │─────────────────────────│ Cybersecurity supply chain risk     │ Parent   GV.SC   │
│         │ ▾ GV  Govern            │ management is integrated into …     │                  │
│         │   ▾ GV.SC  Cybersec…    │ NIST · CSF 2.0 · p. 17 (PDF p. 22)  │ ON THIS PAGE     │
│         │ ▌   GV.SC-03 Cybersec…  │  Source details ▸                   │ Official text    │
│         │     GV.SC-04 …          │─────────────────────────────────────│ Crosswalk (2)    │
│         │   ▸ GV.OC …             │ OFFICIAL CROSSWALK  CSF 2.0 → 1.1   │ References (0)   │
│         │ ▸ ID  Identify          │ ⟂ Multiple crosswalk entries …      │ SOURCE DETAILS ▸ │
│         │                         │ ROW 25 ──▶ [1.1] ID.SC-2 …          │                  │
│         │                         │ ROW 26 ┄┄ ◌ No reference element     │                  │
└─────────┴─────────────────────────┴─────────────────────────────────────┴──────────────────┘

1200–1639px: sidebar 232 | navigator 340/320 | record (no rail)
900–1199px : sidebar 56   | navigator 288     | record (no rail)
<900px     : one screen at a time (list screen → record screen)
```

(The counts in diagrams are illustrative; the UI always renders values from the API.)

### 7.1 Navigator (`surface`, right hairline)

Width 340px at ≥1320px (320px at 1200–1319px, 288px at 900–1199px).

**Header block** (sticky, padding 12×16, bottom hairline):
- **Search field:** 36px tall, full width, `border-strong`, `r-md`. Leading search icon, placeholder "Search ID or text". A `/` keycap hint on the right (hidden on touch devices). Maximum length 200 characters (the API limit). Leading and trailing whitespace is trimmed before the request.
- **Filter row** (8px below): `Level ▾` (Function, Category, Subcategory) and `Function ▾` (the version's functions), each a 28px compact dropdown, plus a "Clear" text button visible only when a filter is active. The `cat` filter is not a dropdown: it is set by a deep link or "Show only this category" on a category record, and appears as a removable chip (for example "GV.SC ✕").
- **Meta line** (`caption`, `text-3`): "{count} elements · CSF {version}" in browse mode; "{count} matches for “{q}” in CSF {version}" in search mode. `count` comes from `ElementList.count`.

**Browse mode** (no `q`): a hierarchical tree built client-side from `parent_id`, rendered with the WAI-ARIA tree pattern.
- Functions appear in NIST order (display constant): CSF 2.0 GV, ID, PR, DE, RS, RC; CSF 1.1 ID, PR, DE, RS, RC. The API orders by `element_id`, so the frontend applies this fixed display order to functions only. Categories and subcategories keep API order. This is presentation-only knowledge and must be documented in code.
- **Function row** (32px): chevron, ID in `id` mono in the version ink, `name` in `ui-sm` 500, subcategory count in `caption`, right-aligned (counted client-side).
- **Category row** (32px, indent 16px): chevron, ID in `id`, `name` truncated with ellipsis (full name in a tooltip).
- **Subcategory row** (32px, indent 32px): `original_id` in `id` mono, then `description` truncated to one line in `text-2`. Subcategories have null `name`, so the description is the label.
- Default: the first function is expanded; ancestors of the selected record are always expanded.
- The navigator tree is loaded from one `GET /catalog/elements?version=…`, cached per version.

**Search mode** (`q` non-empty): a flat list from `GET /catalog/elements?version=…&q=…` (debounced 150ms) in API order, with one display adjustment: an element whose `element_id` or `original_id` equals the query (case-insensitive) is shown first and tagged "Exact ID". The API provides deterministic substring matching over `element_id`, `original_id`, `name` and `description`; no relevance ranking is implied or promised.
- Row (52px, two lines): line 1 is VersionChip, ID, and level (`caption`); line 2 is `name` or `description` on one line, with matched substrings highlighted (`highlight` background; highlighting is display-only, computed client-side).
- Group headings (Functions/Categories/Subcategories) appear only when there are more than 8 results.
- Selecting a result opens the record while the search stays in place (section 8).

### 7.2 Record pane (`surface`)

Padding 32×40 (24×16 below 900px). Content column maximum 720px, left-aligned within the pane. Sections in order: breadcrumb, identity header, official crosswalk, children, informative references.

### 7.3 Facts rail (≥1640px only; `surface-sunken`, left hairline, sticky, 264px)

Two-column definition lists (label 96px in `text-3` `caption`, value in `ui-sm`; mono for IDs and hashes):
- **RECORD:** Version, Level, Printed ID (`original_id`), Normalized ID (`element_id`), Parent (`parent`, as a link).
- **ON THIS PAGE:** anchors to Official text, Crosswalk (with row count), Children (if any), Informative references (with count); the active anchor follows scroll position.
- **SOURCE DETAILS:** a disclosure, collapsed by default (section 9.3).

---

## 8. Browse, search, filter and navigation interactions

### 8.1 URL and history strategy

- Opening a record from the navigator **pushes** a history entry to `/explorer/{version}/{element_id}` and carries the current navigator context (`level`, `fn`, `cat`, `q`) as query parameters. Browser Back therefore returns to the previous URL and restores the same browsing context.
- Typing in search and changing filters **replace** the current entry (debounced for typing), so the history is not flooded with keystrokes.
- Following a crosswalk link to a record in the other version **pushes** an entry; Back returns to the originating record (including its scroll position).
- The `element_id` in a record URL is canonical; a request for the printed spelling (`/explorer/1.1/PR.AT-1`) is accepted (the API normalizes) and the URL is replaced with the normalized `element_id`.
- Ephemeral UI state is stored separately from the URL (session storage, keyed by version): expanded tree nodes, navigator scroll offset, record pane scroll offset. It is restored on Back.
- Do not assume a record was reached through its parent category. A deep link to a record with no navigator context opens with the default tree for that version, with the record's ancestors expanded and the record selected.

### 8.2 Version switching

- The version toggle (header, right) switches the navigator between CSF 2.0 and CSF 1.1. The default on first arrival is 2.0.
- Switching versions **does not** open the same-looking ID in the other version. IDs in the two frameworks are not equivalent, and the crosswalk is the only authoritative relationship.
- Filters on switch: `fn` and `cat` filters that do not exist in the target version are cleared (for example `GV` filters do not carry from CSF 2.0 to CSF 1.1, which has no Govern function). The check uses the target version's element list. `level` and the text search `q` are retained, so a search can be compared across versions. The resulting URL reflects the cleared state, and the switch is a pushed history entry so Back returns to the previous version with its filters.
- If a record was open, it closes and the navigator reloads for the new version. The record pane shows a transient inline hint: "{id} is a CSF {old} element. See its crosswalk section for official relationships to CSF {new}." with a link back to that record. The hint disappears on the next navigation.

### 8.2a Filters that exclude the open record

- The open record is never closed or hidden by a filter or search change. Its detail stays visible and its URL does not change.
- If the active `level`, `fn`, `cat` or `q` exclude the open record, the navigator keeps a pinned row for it at the top of the list, in `neutral-notice` styling with the caption "Selected record is outside the current results", followed by the normal results. The pinned row is not counted in the meta line's count.
- A "Clear filters" action in that pinned row (and the header's "Clear" button) removes the conflicting filters and search; the record stays open and the tree reveals it among its ancestors.
- Deep links and Back behave as in 8.1: a record URL with context parameters that exclude the record opens the record with the pinned-row indicator, and Back restores the earlier context.

### 8.3 Browse

- Chevron or `→`/`←` expands and collapses; clicking a function or category row selects it and opens its record, which shows the official text and its children list. Reading and browsing are the same gesture.
- The Function filter narrows the tree to one function while preserving hierarchy. The Level filter switches to the flat list presentation (levels do not nest in a filtered level view).

### 8.4 Search

- `/` focuses the search field when no text field is focused. `Escape` clears the query (first press) and blurs the field (second press).
- `↓` from the search field moves focus to the first result. `Enter` opens the focused result.
- Empty query returns to the tree and restores the previous expansion state.

### 8.5 Keyboard (Phase 6B acceptance scope)

- Accessible, logical focus order: skip link → sidebar → page header → navigator → record → facts rail.
- Visible focus indicator on all interactive elements (section 3.6).
- `/` to focus search; `Escape` to clear or dismiss (search, popovers, sheets).
- Tree: `↑`/`↓` move between visible rows, `→` expands a collapsed node or moves to its first child, `←` collapses an expanded node or moves to its parent, `Home`/`End` jump to the first/last visible row, `Enter` opens the focused record. Use a roving tabindex and `role="tree"`/`treeitem` with `aria-expanded`, `aria-level` and `aria-selected`.
- On record change, focus moves to the record heading (`h1`, the ID) so assistive technology announces the change.
- A "Skip to record" link is available as the first focusable element on Explorer.

### 8.6 Mobile and narrow navigation (<900px)

- **List screen:** top bar (menu button, "Explorer", version toggle). A sticky search field (40px) and a "Filters" button that opens a bottom sheet with Level and Function. Tree rows are 44px with one-line descriptions.
- **Record screen:** pushed as a new route, so the system Back gesture works. The top bar shows a back control and the record ID in mono. The back label is "Back to results" when navigator context (`q` or filters) came with the URL, and "Browse CSF {version}" otherwise. It does not assume a parent category.
- The breadcrumb is replaced by the back control; the facts and source details become inline disclosures after the official text. Crosswalk entries stack vertically (section 10).
- Returning to the list restores the previous scroll position and expansion state.

---

## 9. Record detail layout

### 9.1 Breadcrumb

`caption`, `text-3`: "CSF 2.0 › Govern (GV) › Cybersecurity Supply Chain Risk Management (GV.SC)". Built from `parent` and parent-of-parent via `function_id`/`category_id`; each ancestor is a link. The record itself is not repeated. Truncates in the middle when narrow (the first and last segments remain).

### 9.2 Identity header

1. **Eyebrow:** VersionChip (e.g. `2.0`), then the level in `label` style (SUBCATEGORY).
2. **ID line:** the printed ID (`original_id`) in `id-lg` mono, with a copy button revealed on hover and focus. If `original_id` differs from `element_id` (CSF 1.1), show a `caption` line "Normalized as {element_id}"; the normalized form is the stable key in URLs and the printed form is what readers know.
3. **Name:** if `name` is non-null (functions and categories), `name-lg`. Subcategories have null `name`; nothing is substituted for it, and the description serves as the headline text.
4. **Official description:** `source-lg` serif in `text-1`, no added quotation marks. If `description` is null (the CSF 1.1 functions), show a `caption` in `text-3`: "NIST CSF 1.1 does not provide a description for this function." Never leave a silent gap and never insert filler text.
5. **Source line** (12px below, always visible): a black `NIST` tag, then "CSF {version} · p. {printed_page} (PDF p. {page})". When `printed_page` is null, show "PDF p. {page}" only. This line identifies the NIST source, the framework version and the page reference next to the text it certifies. It appears in the record header for every record.
6. A "Source details" disclosure follows the source line (section 9.3).

### 9.3 Source details (on demand)

Not shown by default; revealed by the "Source details" disclosure (inline in the record at <1640px, in the rail at ≥1640px; collapsed by default in both). Contents, all from `provenance`:

| Label | Field |
|---|---|
| File | `provenance.source_document.source_file` |
| Section | `provenance.chunk.section` (full path, wrapped) |
| Printed page | `provenance.chunk.printed_page` |
| PDF page | `provenance.chunk.page` |
| Document | `kind`, `pages`, `bytes` from `provenance.source_document` |
| SHA-256 | `provenance.source_document.sha256` (middle-truncated, with copy and the full value revealed on demand) |
| Chunk | `provenance.chunk.chunk_id` |

The backend supplies no source URLs or document-opening capability, so the UI offers none. There is no "Open PDF" action. Crosswalk entries similarly show their `source_file` and `sheet` as text, not links.

### 9.4 Official crosswalk section

Heading by lookup direction (from `crosswalk.lookup`):
- Forward (CSF 2.0 record): "Official crosswalk · CSF 2.0 → CSF 1.1".
- Reverse (CSF 1.1 record): "Referenced by CSF 2.0 · official crosswalk".

Sub-caption: "{n} workbook row(s) · {source_file} · sheet {sheet}" (from the first entry). The `crosswalk.direction` string is available as a tooltip. The derived summary chip (section 10.4) and an "Expand all" control sit on the right of the header. Detailed in section 10.

### 9.5 Children

Shown for functions (categories) and categories (subcategories) from `children`. Heading "Categories (n)" or "Subcategories (n)" (`title-sm`). 40px rows: ID in `id` mono, then `name` or `description` in `source` serif (these are verbatim NIST text), one line expandable to two; each row links to the child. No cards.

### 9.6 Informative references

Section "Informative references (n)" from `informative_references` (verbatim strings, `mono-sm` in `text-2`, one per line). Collapsed by default when n > 6. When the list is empty, show a single `caption`: "No informative references are recorded for this element in ControlShift's data." (In the current data only CSF 1.1 elements carry references.)

---

## 10. CrosswalkEntry and ambiguity presentation

### 10.1 Fields used (`CrosswalkEntry`)

`excel_row`, `sheet`, `source_file`, `focal_version`, `focal_element_id`, `focal_original_id`, `focal_description`, `reference_version`, `reference_element_id`, `reference_original_id`, `reference_description`, `comments`, `strength`, `mapping_type`. Of these, `strength` is always null in current data and is not displayed. `mapping_type` is assigned by ControlShift at ingest (the workbook has no such column) and is always labeled Derived.

### 10.2 Layout

Entries are one bordered list (`r-lg`, hairline-separated rows), in workbook order (as returned), one entry per original workbook row. Rows are never merged, deduplicated or collapsed into a single conclusion.

```
┌──────────────────────────────────────────────────────────────────────┐
│ ROW 25   ───────▶ [1.1] ID.SC-2                      Open record     │
│          Suppliers and third party partners of information systems,  │
│          components, and services are identified, prioritized …      │
│          Show full text                                              │
│          Ingest label: mapped  ┆Derived┆                              │
├──────────────────────────────────────────────────────────────────────┤
│ ROW 26   ┄┄┄┄┄┄┄ ◌ No reference element                              │
│          Workbook comment: “Conceptually new in 2.0”                 │
│          Ingest label: new_in_2_0  ┆Derived┆                          │
└──────────────────────────────────────────────────────────────────────┘
```

- **Gutter (72px):** "ROW {excel_row}" in `mono-sm`, `text-3`. A tooltip reads "Workbook row {excel_row}, sheet {sheet}, {source_file}". The row number is each entry's identity (also its React key).
- **Connector (40px):** a horizontal stroke showing the fixed workbook direction (CSF 2.0 focal → CSF 1.1 reference). Mapped entries: solid, teal to violet. Entries with null `reference_element_id`: dashed `text-4`, ending in the `circle-dashed` icon. The connector direction never flips in the reverse view.
- **Target:**
  - Forward view (CSF 2.0 record): VersionChip `1.1` + `reference_original_id` in mono (printed form, e.g. `ID.SC-2`), with `reference_element_id` (e.g. `ID.SC-02`) revealed in a tooltip and visible on focus; the target links to `/explorer/1.1/{reference_element_id}`. If `reference_element_id` is null: "No reference element" in `text-2` italic Sans, not a link.
  - Reverse view (CSF 1.1 record): the target is the focal CSF 2.0 element (`focal_original_id`, `focal_element_id`, VersionChip `2.0`), linking to `/explorer/2.0/{focal_element_id}`; the current 1.1 record is the arrowhead end.
- **Body (Source Serif, `source`):** the counterpart's official description (`reference_description` in forward view, `focal_description` in reverse view), clamped to 2 lines with "Show full text". If `comments` is non-null: a `caption` "Workbook comment:" followed by the verbatim comment in serif italic. A `NIST` source tag precedes official text; the row's file/sheet are in the tooltip, not repeated per row.
- **Footer:** "Ingest label: {mapping_type}" followed by a dashed `Derived` tag (`mapping_type` values are shown verbatim: `mapped`, `new_in_2_0`, `unmapped`).
- Following a target link pushes history; the destination shows a transient "← From {id} (CSF {v}) · row {n}" return chip above the breadcrumb, driven by navigation state, which disappears on other navigation.
- One-to-many relationships (e.g. ID.IM-03 has multiple entries) appear as separate entries, each with its own row number. All are shown; "Expand all" only expands long descriptions.

**Mobile:** the gutter moves above the target (row number as a small mono label), the connector becomes a vertical stroke or is omitted, and the body spans full width. Tap targets ≥44px.

### 10.3 Ambiguity notice

Displayed when `crosswalk.summary.status === "mapped_and_new_in_2_0"`, above the entries, in the `ambiguous` variant (amber left edge, amber-soft fill, `split` icon). It is generated from the entries, never hard-coded for GV.SC-03.

- **Heading:** "Multiple crosswalk entries require interpretation"
- **Body (template):** "The official transition workbook contains {n} entries for {original_id}. ControlShift preserves all of them and does not choose between interpretations." Then one line per entry, generated from data: "Row {excel_row}: maps to {reference_original_id}." or "Row {excel_row}: has no reference element; comment “{comments}”." (If a row has neither a reference nor a comment, the line says "has no reference element.")
- **Actions:** links "Jump to row {excel_row}" for each entry, scrolling to it and moving focus.
- The wording must not say NIST made an error, must not say the element was removed, and must not state that one row is correct.
- No headline status appears elsewhere for this record: no status badge in the header, no tree icon.

**Acceptance example (GV.SC-03):** row 25 maps to ID.SC-02 (printed `ID.SC-2`); row 26 has no reference and the comment “Conceptually new in 2.0”. Both are visible with equal visual weight, in order 25 then 26, each individually identifiable by row number, with the ambiguity notice above them.

### 10.4 Derived summary chip and no-reference state

The section header shows a dashed pill reading "Derived: {label}", where the label is mapped from `crosswalk.summary.status`:

| `summary.status` | Label |
|---|---|
| `mapped_only` | Derived: mapped only |
| `new_in_2_0_only` | Derived: new in 2.0 only |
| `mapped_and_new_in_2_0` | Derived: mapped and new in 2.0 |
| `no_crosswalk_reference` | Derived: no crosswalk reference |
| `unclassified` | Derived: unclassified |

`crosswalk.summary.note` exists in the API (`CrosswalkSummary.note: str`) and is shown as the chip's tooltip and, on touch devices, in the disclosure beside it. `summary.derived` is always true. The chip's neighbors state that these labels are ControlShift interpretations, not NIST workbook fields. `summary.mapped_row_count`, `new_in_2_0_row_count` and `excel_rows` may be used for counts and the jump links.

**No crosswalk reference** (`entries` empty; occurs for CSF 1.1 elements that no workbook row references): a `neutral-notice` with the `circle-dashed` icon.
- Title: "No crosswalk reference"
- Body: "No row in the official NIST transition workbook references this CSF 1.1 element. The workbook does not state whether the element was retained, merged or dropped."
- Never uses red or amber, and never says "removed", "deprecated", "retired", or "no counterpart". No strikethrough styling.

**New-in-2.0 only** (all entries are `new_in_2_0`): entries render normally, with the target "No reference element" and the workbook comment; no ambiguity notice.

---

## 11. Reusable component specifications

Only components with demonstrated reuse (two or more places) or a distinctive requirement are listed. Do not create further abstractions without a demonstrated need.

**shadcn primitives, themed to the tokens (no structural customization):** `Button`, `Input`, `ToggleGroup`, `DropdownMenu`, `Popover`, `Tooltip`, `Sheet`, `Collapsible`, `ScrollArea`, `Skeleton`, `Separator`.

**Purpose-built components**

| Component | Spec |
|---|---|
| `VersionChip` | `mono-sm` 11/16, padding 1×6, `r-sm`; version soft fill, border and text; content is `2.0` or `1.1` only. Reused on Compare and in Ask citations. |
| `VersionToggle` | An accessible single-selection `RadioGroup` (shadcn/Radix) styled as a segmented control, or an equivalent implementation whose radio-group keyboard behavior has been verified (one tab stop for the group; arrow keys move and select; the group never has zero or two selected values). Exactly one version is always selected; there is no deselected state, and re-activating the selected segment is a no-op. Appearance is unchanged: 28px tall, pill radius on `surface-sunken`; the selected segment is `surface` with border and a 2px underline in the version ink. Labels "CSF 2.0" and "CSF 1.1", 2.0 first; the group has an accessible name ("Framework version"). |
| `ControlId` | Mono, tabular-nums. Props: version, `element_id`, `original_id`. Displays the printed form; reveals the normalized form in a tooltip when they differ. Optional link and copy. Used on all pages. |
| `ElementRow` | Tree variant (32px) and result variant (52px); states per section 3.6. |
| `RecordHeader` | Eyebrow, ID, name, official description (null-safe), source line, Source-details disclosure. |
| `OfficialText` | Serif, sizes `source-lg` and `source`. The only component that uses the serif; accepts an optional source tag slot. |
| `SourceTag` / `DerivedTag` | `SourceTag`: `NIST` (mono 10/14, white on `ink`, `r-sm`) followed by location text. `DerivedTag`: "Derived" with dashed `#B9BCC2` border, `derived` text. A future `GeneratedTag` (Ask) must differ from both in border and fill. |
| `ProvenanceList` | Two-column definition list used in the rail and the inline disclosure; includes the middle-truncated, copyable hash. |
| `CrosswalkEntry` | Section 10. |
| `Notice` | Variants `ambiguous`, `no-reference`, `error`, `info`; `r-lg`, soft fill, 3px left edge in the variant color, icon + `title-sm` + `body` + optional actions. Notices that carry data meaning are not dismissible. |
| `StateBlock` | Empty/error/not-found content: centered column ≤360px, title, one caption line, up to two actions. |

---

## 12. Loading, empty, error and accessibility states

### 12.1 Loading

- Skeletons render only after 150ms to avoid flashes. No shimmer: static `#ECECE7` bars.
- **Navigator:** 8 rows of 32px with varied widths.
- **Record:** when the user selects from the tree, the header renders immediately from the already-loaded `ElementSummary` (`name`, `description`, `original_id`, `level`) and the sections that need `ElementDetail` (source line, crosswalk, children, references) skeleton-load below with matching heights to avoid layout shift. On a direct load, the whole record skeletons.
- **Sidebar status:** neutral dot while `/health` loads.

### 12.2 Empty

- **Initial arrival, no record selected** (CSF 2.0 by default): a compact orientation panel within the 720px column (not a hero): "CSF {version} · {counts.function} functions · {counts.category} categories · {counts.subcategory} subcategories" from `GET /catalog/versions`, a sentence stating that records are official NIST text and labels marked Derived are ControlShift interpretations, and three text links to example records that exist in the data: `GV.SC-03` (CSF 2.0; two crosswalk entries), `ID.IM-03` (CSF 2.0; several crosswalk entries, one per workbook row), and `RC.CO-02` (CSF 1.1; no crosswalk reference). No record is preselected.
- **Empty search:** in the navigator, a `StateBlock`: "No elements match “{q}” in CSF {version}" with actions "Search CSF {other version} instead" and "Clear search".
- **Empty filter result:** "No elements match these filters" with "Clear filters".
- **Empty children/references:** per sections 9.5 and 9.6.

### 12.3 Errors and not found

Errors use the API's envelope `{"error": {"code", "message", "details"}}` and render inline in the failing region (never as raw JSON or stack text), with `message` shown in `caption`.

| Situation | Presentation |
|---|---|
| Record not found (`404`, `code: "not_found"`) | `StateBlock`: "{id} was not found in CSF {version}"; action "Search for “{id}”". No retry. |
| Invalid filter or path version (`422`, `code: "invalid_request"`) | "That filter isn't valid" and a "Reset filters" action. |
| Server error (`500`, `internal_error`) or other failures | `error` Notice with "Retry". |
| Proxy/network failure | Region banner "ControlShift API is unreachable" with "Retry"; the sidebar status turns to `error`. Cached navigator data, if present, remains with a caption "Showing cached results". |

### 12.4 Accessibility requirements

- Text contrast ≥4.5:1; `text-4` is never used for information.
- Version, derived status, and ambiguity are never conveyed by color alone: each has text.
- The tree implements the WAI-ARIA tree pattern (section 8.5). The version toggle is a single-selection radio group (section 11). Overlays follow their accessibility pattern:
  - **Modal sheets and dialogs** (the mobile navigation sheet, the filters sheet) contain keyboard focus while open: focus moves into the overlay on open, `Tab`/`Shift+Tab` cycle within it, the page behind is inert, `Escape` and an explicit close control dismiss it, and focus returns to the control that opened it.
  - **Non-modal popovers and menus** (the sidebar status popover, the Level/Function dropdowns, tooltips) do not intentionally trap focus. They support the keyboard navigation appropriate to their pattern (menus use arrow keys; popovers are reachable in the normal tab order), `Escape` dismisses them, and focus returns to the trigger when they were opened from it. Moving focus out of a popover closes it.
- Notices use `role="status"` (informational) or `role="alert"` (errors). Loading regions set `aria-busy`.
- Respect `prefers-reduced-motion`. Use semantic landmarks: `nav` (sidebar), `main` (workspace), `region` labels for navigator and record.
- Zoom to 200% without loss of content or horizontal scroll.

---

## 13. Backend API integration assumptions

Verified against `src/controlshift/api/catalog.py` (commit `4eec74f`). The browser calls the Next.js same-origin proxy; the proxy path prefix is a Phase 6B implementation decision and no CORS is required. The frontend uses hand-written TypeScript types mirroring these models; fields not listed here are not used.

**`GET /catalog/versions` → `VersionList { versions: VersionInfo[] }`**
`VersionInfo { version: "1.1"|"2.0", name, source_document: SourceDocument, counts: { function, category, subcategory }, total_elements }`.
`SourceDocument { source_file, kind, sha256, bytes, pages: number|null }`.

**`GET /catalog/elements` → `ElementList { count, elements: ElementSummary[] }`**
Query parameters: `version` ("1.1"|"2.0"), `level` ("function"|"category"|"subcategory"), `function` (two letters), `category` (e.g. `GV.SC`), `q` (≤200 characters). Case-insensitive substring match over `element_id`, `original_id`, `name`, `description`. Ordered by `(version, element_id)`. No pagination (about 270 elements total). Invalid values return 422 in the error envelope.
`ElementSummary { version, element_id, original_id, level, name: string|null, description: string|null, function_id, category_id: string|null, parent_id: string|null }`.

**`GET /catalog/elements/{version}/{element_id}` → `ElementDetail`**
`ElementDetail = ElementSummary & { parent: ElementSummary|null, children: ElementSummary[], informative_references: string[], provenance: { source_document: SourceDocument, chunk: { chunk_id, page: number, printed_page: string|null, section } }, crosswalk: Crosswalk }`.
`Crosswalk { direction: "CSF 2.0 (focal) -> CSF 1.1 (reference)", queried_role: "focal"|"reference", lookup: "forward"|"reverse", entries: CrosswalkEntry[], summary: CrosswalkSummary }`.
`CrosswalkEntry { excel_row, sheet, source_file, focal_version, focal_element_id, focal_original_id, focal_description: string|null, reference_version, reference_element_id: string|null, reference_original_id: string|null, reference_description: string|null, comments: string|null, strength: string|null, mapping_type: "mapped"|"new_in_2_0"|"unmapped" }`.
`CrosswalkSummary { derived: true, status: "mapped_only"|"new_in_2_0_only"|"mapped_and_new_in_2_0"|"no_crosswalk_reference"|"unclassified", mapped_row_count, new_in_2_0_row_count, excel_rows: number[], note }`.
Element IDs accept the printed or normalized spelling and any letter case. Unknown IDs return 404 `not_found`; an invalid version in the path returns 422.

**`GET /health`** (sidebar status only): `{ status, database: { chunks, elements, crosswalk_rows }, retrieval: { mode, models_loaded }, llm: { configured, provider, model } }`.

**Error envelope:** `{ error: { code: string, message: string, details: { field, problem }[] | null } }`.

**Notes**
- There is no endpoint for listing all crosswalk rows, source documents, or the document files themselves. Do not design UI that implies them.
- `/ask` and `/compare` are not used by Explorer.
- Search highlighting, "Exact ID" ordering, function ordering, subcategory counts and breadcrumb assembly are client-side presentation derived from API data; they do not change what the API returns.

---

## 14. Consistency rules for future pages (brief)

Each page below will get its own detailed specification.

- **Overview:** a reading page (≤1080px on `canvas`). Content must be real: dataset facts from `/catalog/versions` and `/health`, the three working destinations with one sentence each, and a legend of the three source labels (official, derived, AI-generated). No charts or fabricated metrics.
- **Ask ControlShift:** a research-document layout, not chat bubbles. The question is the page header; the answer is Sans text under an `AI-generated` tag together with the API's `disclaimer`. Citations link to evidence shown with `OfficialText`, `SourceTag` and `VersionChip`; crosswalk evidence reuses `CrosswalkEntry`. Statuses `abstained`, `evidence_only` and `rejected` use `Notice` variants (HTTP 200 responses are interpreted by `status`). The serif is never used for generated text.
- **Compare Frameworks:** reuses `VersionChip`, `CrosswalkEntry` and the Derived labeling. A full crosswalk listing requires a backend route that does not exist yet; until then the page is an honest "Soon" placeholder. It must not mock data.
- All pages share the shell, the tokens, the source-label system (section 2), the `Notice`/`StateBlock` patterns, and the rule that each page defines its loading, empty and error states.

---

## 15. Visual quality acceptance criteria

A screen passes only if all hold:
1. **Typography:** only tokens from section 3.2 are used. Serif appears only on verbatim NIST/workbook text; mono only on identifiers; no weight above 600; default UI text is 14px.
2. **Alignment:** edges sit on the 4px grid; navigator rows, record column and rail labels share consistent insets; pane borders meet cleanly with no off-by-one seams.
3. **Density:** rows are 32/52px (≥44px below 900px); no unexplained empty region over 96px; no cards inside cards.
4. **Hierarchy:** within two seconds a reviewer can state the record's ID, version, source page and crosswalk row count.
5. **Responsive:** layout follows section 5 with no horizontal scroll, overlap, or information lost without a reveal at every tested width.
6. **Keyboard:** the loop search → open → read crosswalk → follow a link → go back works without a mouse, with visible focus throughout (section 8.5).
7. **States:** every region has loading, empty and error states; none shows raw JSON or stack text.
8. **Provenance and citation clarity:** official text always has the `NIST` source line, version and page within one glance; every derived label includes the word "Derived"; GV.SC-03 shows rows 25 and 26 with equal weight; no UI text calls a missing reference "removed".
9. **Consistency:** no ad-hoc hex values, radii or shadows; shadcn defaults visibly overridden.
10. **Not generic:** no gradients, glows, emoji, sparkle icons, chat bubbles, decorative charts, or card grids on working pages.

---

## 16. Screenshot review requirements

- **Tooling:** a Playwright script captures the fixed routes below at 1920×1080, 1640×900, 1440×900, 1280×800, 1200×800, 1024×768, 900×800, 768×1024 and 390×844 (initial targets; add or drop widths if breakpoints change).
- **Data:** API responses are recorded once from the real local API into fixtures so captures are deterministic.
- **Fixture set:** arrival (2.0); `GV.SC-03` (ambiguity); `ID.IM-03` (many entries); `PR.AT-1` / `PR.AT-01` (CSF 1.1, differing spellings, informative references); a function with children (`GV`); a CSF 1.1 function (null description); `RC.CO-02` in CSF 1.1 (no crosswalk reference); search "supply"; empty search; filtered browse (function filter); 404; API unreachable; loading (delayed responses); the mobile list and record screens.
- **Process:** after each component or region lands, capture, score against section 15 in a short table (pass/fail per criterion with a note), and keep before/after images in the pull request. Layout breakpoints are confirmed or adjusted from these captures. Keyboard behavior is checked manually in the browser (the full loop in criterion 6) in addition to screenshots.

---

## 17. Deferred design enhancements

Not Phase 6B acceptance requirements:
- Sibling navigation (previous/next record), a global copy-ID shortcut, and a keyboard shortcut to toggle the sidebar.
- Dark theme (tokens are structured to allow it).
- A full crosswalk listing and Compare Frameworks views (need a `/crosswalk` backend route).
- Client-side search for faster feedback (only if server search latency proves noticeable; it must mirror server semantics and be documented).
- Opening source PDFs or linking to documents (needs backend and licensing support).
- Detailed Overview, Ask ControlShift and Compare specifications.
