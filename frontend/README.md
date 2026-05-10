# Frontend — Nexus-Diagnostix

React 18 + Vite + TypeScript + TailwindCSS + shadcn/ui.

## Démarrage local

```bash
npm install
npm run dev    # → http://localhost:5173
```

## Tests

```bash
npm test            # vitest + couverture (100 % exigée)
npm run test:e2e    # Playwright (3 navigateurs)
```

## Qualité

```bash
npm run type-check  # tsc --noEmit
npm run lint        # eslint
npm run format      # prettier
```

## Structure

```
src/
├── pages/         # 1 fichier par route
├── components/    # ui (shadcn) + métier (questionnaire, report, admin)
├── hooks/         # custom hooks
├── lib/           # api client, utils, auth
├── styles/        # globals.css (Tailwind)
├── App.tsx        # routes
└── main.tsx       # entry point
```

## Charte visuelle

- **Orange** : `#FF5A1F` (NexusRH)
- **Noir** : `#0A0A0A`
- **Gris** : `#F4F4F5`
- **Typo** : Inter (corps), Space Grotesk (titres)

Voir [`../CLAUDE.md`](../CLAUDE.md) §9 pour les règles UX/UI complètes.
