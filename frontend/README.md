# Frontend - Clinical Handover Dashboard

A high-fidelity React dashboard for real-time monitoring of clinical AI agents.

## Design Language

- **Glassmorphism**: Translucent backdrops and soft shadows for a premium, clinical feel.
- **Dynamic Animations**: Radar-pulse effects indicate active AI processing.
- **SVG Wireframes**: High-precision medical icons for every agent node.

## Key Components

- **TaskGraph**: powered by **React Flow**, visualizing the LangGraph state machine mapping in real-time.
- **SbarPanel**: A categorized output view with triage-colored headers and doctor intervention capabilities.
- **MessageFeed**: A chronological log of every clinical reasoning step taken by the AI.

## Setup & Running

```bash
cd frontend
npm install
npm run dev
```

## State Management
- **WebSocket**: Direct integration with the FastAPI backend for instant UI state updates.
- **Axios**: Standard HTTP requests for PDF uploads and feedback submission.
