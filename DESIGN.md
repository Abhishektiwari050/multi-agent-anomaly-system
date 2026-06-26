---
version: alpha
name: Aura Clinical System
description: A premium, clinical-focused dark mode interface designed for real-time patient anomaly analysis. It leverages subtle glassmorphism and clear color indicators to prioritize information hierarchy.
colors:
  primary: "#0B0F19"
  secondary: "#94A3B8"
  accent: "#10B981"
  danger: "#EF4444"
  warning: "#F59E0B"
  neutral: "#FFFFFF"
  card-bg: "rgba(15, 23, 42, 0.45)"
  border-muted: "rgba(255, 255, 255, 0.08)"
typography:
  body:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  heading:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.2
  label:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.3
rounded:
  sm: 6px
  md: 12px
  lg: 24px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
components:
  card-glass:
    backgroundColor: "{colors.card-bg}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  btn-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.neutral}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  status-badge:
    rounded: "{rounded.full}"
    padding: "4px 12px"
---

## Overview

The Aura Visual Identity is designed for modern clinical dashboards that display multi-agent diagnostic information. Since clinical staff need to make quick decisions, the design prioritizes high contrast, clear information hierarchy, and intuitive color-coding. The system utilizes a deep dark slate foundation (#0B0F19) combined with translucent glassmorphic components to feel premium, calm, and futuristic.

## Colors

The palette is optimized for dark environments and immediate visual alert routing:

- **Primary (#0B0F19):** A deep, dark slate backing that minimizes eye strain during long monitoring shifts.
- **Secondary (#94A3B8):** Steel/slate gray used for helper text, labels, and borders.
- **Accent (#10B981):** A vibrant emerald green indicating active scans, clean health, and resolved statuses.
- **Danger (#EF4444):** A medical warning red indicating a high count of severe patient anomalies.
- **Warning (#F59E0B):** A clinical warning amber/orange indicating moderate vital anomalies requiring review.
- **Neutral (#FFFFFF):** High contrast white for core values and readability.

## Typography

The typography system is simple and legible:

- **Font Family:** Plus Jakarta Sans (loaded via Google Fonts) is the default clinical typeface. It has clean proportions that remain highly legible at small sizes.
- **Scale:**
  - **Headings (`##`):** 28px, Bold (600), line-height 1.2, tracking -0.01em.
  - **Body Text:** 14px, Regular (400), line-height 1.5.
  - **Metadata & Labels:** 12px, Medium (500), line-height 1.3.

## Layout

The screen uses a split dashboard layout:
- **Sidebar (Width: 320px):** Handles historical tasks and scan creation.
- **Main Area (Flex: 1):** Displays live status progress, metric charts, and vital records detail.
- **Grids:** 2-column or 3-column responsive grid formats are used to separate vitals graphs from patients list.

## Elevation & Depth

Layering is achieved through varying translucent styles and borders instead of heavy box-shadows:
- **Level 1 (Base):** Flat dark backdrop.
- **Level 2 (Panels):** Translucent card backing (`rgba(15, 23, 42, 0.45)`) combined with a faint border (`rgba(255, 255, 255, 0.08)`) and backdrop blur filter of `16px`.
- **Level 3 (Alerts):** Strong neon borders (`#EF4444` or `#F59E0B`) mapping directly to clinical anomaly alert severities.

## Shapes

- **Controls & Buttons:** Rounded with a small radius (`6px`) to feel precise and professional.
- **Containers & Cards:** Rounded with a medium radius (`12px`) for a clean, friendly look.
- **Pills & Badges:** Rounded with full radius (`9999px`) for standard pill badges.

## Components

- **Card Glass:** A base container for modules. Uses thin gray borders and translucent backdrops.
- **Button Primary:** Emerald green block button with a slight transition on hover.
- **Status Badge:** A clean pill indicator that uses transparent colors overlaid on background-color fills.

## Do's and Don'ts

- **Do:** Use the Emerald color (`#10B981`) exclusively for positive states (running scans, system online, safe patients).
- **Do:** Highlight critical alarms immediately using high-intensity red borders.
- **Don't:** Mix multiple bright accent colors in a single view; use gray/slate text to keep the view clean.
- **Don't:** Use solid, non-transparent light gray backgrounds in cards as it breaks the glassmorphism aesthetic.
