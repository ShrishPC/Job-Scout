# Job Scout: UI/UX Design Language & Favicon Generation Spec

This document details the visual style, design system tokens, and geometry rules for the **Job Scout** platform, followed by optimized prompts to generate a matching favicon in Gemini Web or other image generators.

---

## 🎨 1. Core Visual Style: Neo-Brutalist Cyber-Retro

Job Scout uses a **Neo-Brutalist** design language. Unlike modern, smooth, and minimalist SaaS templates, Neo-Brutalism emphasizes raw structure, high contrast, flat shapes, and thick borders. It blends a warm, retro cream background with high-saturation cyberpunk accents.

### Color Palette

| Color Token | Hex Code | Purpose |
|---|---|---|
| **Base Cream (Background)** | `#FDFBF7` | Warm, comfortable background color (replacing stark white) |
| **Thick Outline / Text** | `#000000` | Pure black, used for all outlines, borders, and main body text |
| **Retro Yellow (Primary Accent)**| `#FFDE4D` | Highlight badges, main logo container |
| **Retro Red/Orange (Call-To-Action)**| `#FF4C4C` | Buttons, alerts, negative action indicators |
| **Retro Mint/Green (Status/Success)**| `#3D8B37` | Skill tags, active resume indicator, success state |
| **Midnight Cyber (Dark Theme)** | `#0D0E15` | Theme toggle background, cyber grid paper background |

### Geometric Rules (The Box Model)
* **Outlines**: Every card, input field, and button has a solid `3px` or `4px` black border (`border: 3px solid #000000`).
* **Shadows**: No soft blur shadows. All shadows are **flat, solid black offsets** shifted down and right by 3px or 4px (`box-shadow: 3px 3px 0px 0px #000000`).
* **Tactile Press Effect**: Active states shift the buttons down and right while removing the shadow to simulate a physical button click:
  `transform: translate(3px, 3px); box-shadow: none;`
* **Grid Pattern**: A subtle dot-grid background (`radial-gradient(#000000 1px, transparent 1px) 20px 20px`) runs globally, giving a draft-paper/cyberpunk feeling.

---

## ⚙️ 2. Favicon Concept & Geometry

The favicon must represent "job discovery" (a radar, compass, target, or scout badge) within the flat, bold Neo-Brutalist theme.

### Graphic Principles
1. **Flat Design**: No 3D gradients, realistic lighting, bevels, or soft shadows.
2. **Thick Outlines**: The graphic element must have a prominent, thick black outer stroke.
3. **High Contrast**: Simple shapes using the yellow, red, and cream palette.
4. **Legibility**: It must remain distinct and recognizable at small sizes (16x16 or 32x32 pixels).

---

## 🖼️ 3. Image Generation Prompts for Gemini Web

Copy and paste one of the following prompts into Gemini Web (or DALL-E / Midjourney) to generate the asset.

### Option A: Neo-Brutalist Radar Badge (Recommended)
> **Prompt**: A flat vector favicon icon of a radar dish detecting a star, designed in a bold Neo-Brutalist style. Crisp pure white background. The icon is a simple circular radar badge with a thick solid black outer outline. It has a flat offset black drop shadow. Color palette: safety orange, retro yellow, cream, and pure black. Clean geometry, no gradient shading, 2D vector, graphic illustration style.

### Option B: The Job Scout Compass/Target
> **Prompt**: A 2D flat vector icon of a compass targeting a magnifying glass, Neo-Brutalist design. Isolated on a white background. Thick black borders, high-contrast flat block colors of warm cream, retro red, and bright yellow. Flat black shadow offset. Minimalist, bold lines, retro sticker style.

### Option C: Minimalist "J" Badge
> **Prompt**: A bold letter "J" styled as a scout badge, flat Neo-Brutalist visual language. Single letter vector logo. Solid black heavy outline, bright yellow background filling the badge shape, with a flat black 3D shadow offset. 2D vector graphic, clean borders, high contrast.
