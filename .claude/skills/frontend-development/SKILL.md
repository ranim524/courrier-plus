---
name: frontend-development
description: React + TypeScript + Vite + Tailwind conventions for Courrier+
---

# Frontend Development

## Purpose
Keep the React frontend modular, typed, and consistent with the Courrier+ visual identity.

## When to use it
Any time you touch `frontend/src/`.

## Project conventions
- Vite + React + TypeScript (strict mode). Tailwind CSS for styling. React Router for routing.
- `src/pages/` — one component per route, thin: composes layout + components + hooks, holds page-level state.
- `src/components/` — reusable presentational/UI pieces (Button, Input, StepProgress, Timeline, StatusBadge, etc).
- `src/layouts/` — shared page shells (PublicLayout with header/footer, AdminLayout with sidebar).
- `src/services/` — one file per backend resource (`letters.ts`, `payments.ts`, `tracking.ts`, `access.ts`, `admin.ts`), wrapping a shared `apiClient` (axios instance with base URL from `import.meta.env.VITE_API_URL`).
- `src/types/` — TypeScript interfaces mirroring backend Pydantic schemas.
- `src/hooks/` — reusable stateful logic (`useSendLetterWizard`, `useAuth`).
- The multi-step "send letter" flow keeps its accumulated state in a single context/hook (`useSendLetterWizard`), not in the URL or in each page in isolation — each step page reads/writes to it.

## Important rules
- No `any` unless truly unavoidable (document why with a one-line comment).
- Never trust client-side validation alone — the backend re-validates everything, but the frontend must still validate for good UX.
- Never render raw HTML from user/admin input (avoid `dangerouslySetInnerHTML`) — prevents XSS.
- Keep the visual identity: professional, trustworthy, minimal. Primary brand color palette defined once in `tailwind.config.js`, reused everywhere (no ad hoc hex codes in components).
- All pages must be responsive (mobile-first Tailwind breakpoints).

## Workflow for a new page
1. Add route in `src/App.tsx` (or router config file).
2. Add/extend type in `src/types/`.
3. Add/extend service function in `src/services/`.
4. Build the page using existing components where possible; add new components to `src/components/` if reusable.
5. Handle loading/error/success states explicitly.

## Branding
Name: **Courrier+**. Tone: professional digital registered-mail service for Tunisia. Avoid childish or generic "AI-template" look — commit to a real color scheme and typography defined in `tailwind.config.js` and reused consistently across app + emails.
