# Job Scout - Next.js Frontend

The Job Scout frontend is a Neo-Brutalist web application built with **Next.js 16 (App Router)**, **React 19**, **Tailwind CSS**, and **Lucide React** icons.

---

## 🎨 Views & Modules

- **🎯 Job Hunt (`/`)**: Real-time matched job feed powered by hybrid neural search (pgvector + keyword ranking).
- **🕸️ Radar View**: Interactive SVG radar chart mapping candidate skills against live industry demand.
- **💼 Application Pipeline**: Drag-and-drop Kanban board for managing application stages (*Interested*, *Applied*, *Interviewing*, *Offered*, *Rejected*).
- **🗄️ Resume Vault**: Multi-resume storage and activation with instant **PDF** and **DOCX** export.
- **✨ AI Copilot**: Tailored resume and cover letter generator with direct one-click document exports.
- **🛡️ Admin Telemetry (`/admin`)**: System dashboard with hardware monitor, cache controls, and indexing velocity metrics.

---

## 🚀 Development Setup

```bash
# Install dependencies
npm install

# Start development server with Turbopack
npm run dev

# Production build check
npm run build
```

---

## 🔗 Environment Variables

Configure `.env.local` or root `.env`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```
