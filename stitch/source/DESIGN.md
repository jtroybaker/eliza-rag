# Design System Specification: The Editorial Intelligence Framework

## 1. Overview & Creative North Star
**Creative North Star: "The Cinematic Curator"**

This design system moves away from the clinical, "SaaS-blue" aesthetics of traditional AI tools. Instead, it draws inspiration from high-end editorial magazines and cinematic interfaces. It treats information not as "data" to be processed, but as "content" to be curated. 

The system breaks the standard "dashboard" look through **intentional asymmetry**, where large editorial typography is offset by hyper-functional UI controls. We lean into deep tonal depth and generous negative space to create a "zen-like" environment for deep research and synthesis. This is enterprise-grade power wrapped in a luxury, minimalist aesthetic.

---

## 2. Colors & Surface Philosophy
The palette is built on a foundation of "Ink and Light." We use a spectrum of near-blacks to create depth, punctuated by surgical strikes of crimson.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning content. To define boundaries, designers must use:
1. **Background Color Shifts:** Moving from `surface` to `surface_container_low`.
2. **Tonal Transitions:** Defining an area through a slightly lighter or darker panel.
3. **Negative Space:** Using the spacing scale to create invisible boundaries.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of fine, dark paper.
*   **Base Level:** `surface` (#111416) - The foundation.
*   **The "Work" Layer:** `surface_container_low` (#191C1E) - For large content areas.
*   **The "Focus" Layer:** `surface_container` (#1D2022) - For cards and citation blocks.
*   **The "Interaction" Layer:** `surface_container_highest` (#323537) - For active states and hover triggers.

### The Glass & Gradient Rule
To achieve a "signature" feel, floating elements (modals, dropdowns, floating toolbars) must utilize **Glassmorphism**:
*   **Formula:** `surface_container` at 70% opacity + `backdrop-blur(20px)`.
*   **Gradients:** Use subtle linear gradients from `primary` (#FFB3B6) to `primary_container` (#E11D48) on high-value CTAs to give them a "lit-from-within" glow.

---

## 3. Typography
The system utilizes a high-contrast pairing of a dramatic serif and a functional sans-serif to bridge the gap between "Tech" and "Editorial."

*   **Editorial Serif (Newsreader):** Used for all `display` and `headline` tokens. This communicates authority, history, and sophistication. It should feel like a masthead.
*   **Functional Sans (Manrope):** Used for `title`, `body`, and `label` tokens. It provides the high-legibility clarity required for complex AI-generated text and RAG citations.

### Hierarchy & Scale
*   **Display Large (Newsreader, 3.5rem):** Use for hero moments or empty-state greetings.
*   **Headline Medium (Newsreader, 1.75rem):** The standard for AI-generated response headers.
*   **Body Large (Manrope, 1rem):** The default for long-form RAG results. Line height should be generous (1.6) to ensure an editorial reading experience.
*   **Label Medium (Manrope, 0.75rem, All Caps):** Used for metadata, status chips, and overlines.

---

## 4. Elevation & Depth
Depth in this system is achieved through **Tonal Layering** rather than structural geometry.

*   **The Layering Principle:** Place a `surface_container_lowest` (#0C0F11) card inside a `surface_container_low` (#191C1E) section. This "recessed" look creates a natural focus area without needing a shadow.
*   **Ambient Shadows:** For floating elements, use a "Super-Soft Glow":
    *   `box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);`
    *   The shadow should feel like a soft weight rather than a hard edge.
*   **The Ghost Border:** If accessibility requires a border (e.g., in low-contrast environments), use `outline_variant` at 15% opacity. Never use 100% opaque borders.

---

## 5. Components

### Large Focused Text Inputs
The AI prompt is the most important interaction.
*   **Styling:** No border. Background: `surface_container_high`.
*   **Radius:** `xl` (1.5rem).
*   **Interaction:** On focus, the background transitions to `surface_container_highest` with a 1px `primary` ghost-border.

### Elegant Segmented Controls
Used for switching between "Search," "Synthesize," and "Source" modes.
*   **Styling:** A single pill-shaped container using `surface_container_lowest`.
*   **Active State:** A `surface_container_high` pill that slides underneath the text labels with a soft spring animation.

### Citation & Result Blocks
To avoid clutter in RAG outputs:
*   **Styling:** Forbid dividers. Use `surface_container_low` for the citation block with a `primary` left-border accent (2px wide) to indicate relevance.
*   **Layout:** Use generous padding (24px) to let the typography breathe.

### Buttons
*   **Primary:** Background: `primary_container` (#E11D48). Text: `on_primary_container`. 
*   **Secondary:** Background: `surface_variant`. Text: `on_surface`.
*   **Ghost:** No background. Text: `primary`.

---

## 6. Do's and Don'ts

### Do:
*   **Do** use asymmetrical margins. For example, a wide left margin for a main heading with a narrow right column for metadata.
*   **Do** lean into the "Rose" accents (`primary_container`) sparingly. It should feel like a signature, not a primary theme.
*   **Do** use `body-lg` for AI responses to prioritize legibility and a premium reading feel.

### Don't:
*   **Don't** use 1px dividers between list items. Use 16px–24px of vertical white space or a subtle `surface` shift.
*   **Don't** use pure white (#FFFFFF). Always use `on_surface` (#E1E2E5) or `on_surface_variant` for a softer, more sophisticated contrast.
*   **Don't** use sharp corners. Every element must adhere to the `lg` (1rem) or `xl` (1.5rem) roundedness scale to maintain the "luxury" feel.