# Maintolio Frontend

Unified role-aware frontend for the Maintolio DRF backend.

## Stack

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form + Zod
- Recharts
- Sonner
- lucide-react

## Setup

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

The frontend expects the backend at:

```text
MAINTOLIO_BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_BASE_URL=
```

Local browser requests use the Next.js `/api/*` rewrite proxy by default, so the Django backend does not need CORS enabled for local development.

Run the backend first:

```bash
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo_data
```

Then open:

```text
http://127.0.0.1:3000
```

## Demo Login

```text
owner@techcare.test / Test@12345
admin@techcare.test / Test@12345
manager@techcare.test / Test@12345
technician1@techcare.test / Test@12345
rahim@abchospital.test / Test@12345
```

## Commands

```bash
npm run dev
npm run lint
npm run build
npm run test
npm run e2e
```

Modern frontend packages currently warn when Node is below `20.19.0`. Use Node `20.19+`, `22.13+`, or a current LTS if you want a warning-free install.
