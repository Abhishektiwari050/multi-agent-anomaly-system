---
version: alpha
name: Aura Clinical Light
description: A premium, clinical-focused light mode interface designed for real-time patient anomaly analysis. It utilizes a clean off-white background with subtle border highlights and readable, accessible color indicators.
colors:
  primary: "#F8FAFC"
  secondary: "#475569"
  accent: "#0F766E"
  danger: "#DC2626"
  warning: "#B45309"
  neutral: "#0F172A"
  card-bg: "rgba(255, 255, 255, 0.75)"
  border-muted: "rgba(15, 23, 42, 0.08)"
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
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  status-badge:
    rounded: "{rounded.full}"
    padding: "4px 12px"
---

## Overview

The Aura Visual Identity Light theme is designed for modern clinical dashboards that display multi-agent diagnostic information in well-lit medical environments. Since clinical staff need to make quick decisions without eye fatigue, the design uses a clean, calm off-white base (#F8FAFC) paired with highly legible typography. Information hierarchy is defined using thin borders, soft shadows, and WCAG AA contrast-compliant color badges.

## Colors

The palette is optimized for clean readability and quick visual alert routing:

- **Primary (#F8FAFC):** A soft, subtle off-white/cool slate backing that feels clean and spacious.
- **Secondary (#475569):** Mid-tone slate gray for captions, borders, and secondary descriptions.
- **Accent (#0F766E):** A deep medical teal for status-positive indicators, active scans, and primary buttons.
- **Danger (#DC2626):** A deep red indicating high-severity patient vital anomalies.
- **Warning (#B45309):** A dark amber indicating moderate vital warning alerts.
- **Neutral (#0F172A):** Very dark blue-slate for high contrast primary text.

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

Layering is achieved through soft shadows and thin borders instead of dark overlays:
- **Level 1 (Base):** Soft slate backing.
- **Level 2 (Panels):** Translucent white card backing (`rgba(255, 255, 255, 0.75)`) combined with a thin border (`rgba(15, 23, 42, 0.08)`) and backdrop blur filter of `16px`. Uses soft shadows.
- **Level 3 (Alerts):** Strong colored left borders (`#DC2626` or `#B45309`) mapping directly to clinical anomaly alert severities.

## Shapes

- **Controls & Buttons:** Rounded with a small radius (`6px`) to feel precise and professional.
- **Containers & Cards:** Rounded with a medium radius (`12px`) for a clean, friendly look.
- **Pills & Badges:** Rounded with full radius (`9999px`) for standard pill badges.

## Components

- **Card Glass:** A base container for modules. Uses thin gray borders and translucent backdrops.
- **Button Primary:** Emerald green block button with a slight transition on hover.
- **Status Badge:** A clean pill indicator that uses transparent colors overlaid on background-color fills.

## Do's and Don'ts

- **Do:** Ensure all status colors (teal, amber, red) meet WCAG AA contrast ratios (at least 4.5:1) against the off-white card backgrounds.
- **Do:** Use subtle border highlights to demarcate sections instead of deep dark backgrounds.
- **Don't:** Use pure white text on light backgrounds; always use Slate 900 (#0F172A) for body text readability.
- **Don't:** Rely on pure black borders; use semi-transparent grays (`rgba(15, 23, 42, 0.08)`) for smooth transitions.
