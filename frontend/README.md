# TechMindd-AI Dashboard

## Development

```bash
npm install
cp .env.example .env
npm run dev
```

The dashboard runs at `http://localhost:5173` and expects the FastAPI service at
`http://localhost:8000` by default. Override it with `VITE_API_URL`.

## Production build

```bash
npm run build
```
