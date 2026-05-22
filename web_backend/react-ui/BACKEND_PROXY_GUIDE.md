# Backend Proxy and API Contract Layer Implementation

## Overview

Stage 3B-B/6B-B implements a secure backend proxy and API contract layer that separates the frontend from direct AI service integration. This ensures API keys and sensitive configuration remain server-side only.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │             Services Layer (TypeScript)                    │ │
│  │  - transcriptionService.ts                                 │ │
│  │  - summaryGenerationService.ts                             │ │
│  │  - apiClient.ts                                            │ │
│  └──────────────────────┬─────────────────────────────────────┘ │
│                         │                                       │
│                         │ HTTP/JSON                             │
│                         ▼                                       │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ Vite Proxy: /api → http://localhost:8000
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              API Routes (api_routes.py)                    │ │
│  │  POST /api/v1/transcribe                                   │ │
│  │  POST /api/v1/summarize                                    │ │
│  │  GET  /api/v1/providers/info                              │ │
│  │  GET  /api/v1/health                                      │ │
│  └──────────────────────┬─────────────────────────────────────┘ │
│                         │                                       │
│  ┌──────────────────────┴─────────────────────────────────────┐ │
│  │           Provider Adapter Layer                           │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │ │
│  │  │  Transcription  │  │     Summary     │                 │ │
│  │  │    Provider     │  │    Provider     │                 │ │
│  │  └────────┬────────┘  └────────┬────────┘                 │ │
│  │           │                     │                          │ │
│  │    ┌──────┴──────┐       ┌─────┴─────┐                     │ │
│  │    │  Whisper    │       │   LLM     │                     │ │
│  │    │  (Real ASR) │       │ Provider  │                     │ │
│  │    └─────────────┘       │(OpenAI/   │                     │ │
│  │                          │ Ollama)   │                     │ │
│  │                          └───────────┘                     │ │
│  │    ┌────────────────────────────────────────┐              │ │
│  │    │         Fallback Providers             │              │ │
│  │    │ (Mock transcription, template summary) │              │ │
│  │    └────────────────────────────────────────┘              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Provider Adapter Layer (Backend)

Located in `backend/providers/`:

- **base.py**: Base provider interface and result types
  - `ProviderType`: Enum for FALLBACK, BACKEND, MANUAL
  - `ProviderResult`: Standardized result wrapper
  - `BaseProvider`: Abstract base class for all providers

- **transcription.py**: Audio transcription providers
  - `FallbackTranscriptionProvider`: Mock transcription
  - `WhisperTranscriptionProvider`: Real ASR via Whisper
  - `TranscriptionProvider`: Factory class

- **summary.py**: Summary generation providers
  - `FallbackSummaryProvider`: Template-based simple summary
  - `LLMSummaryProvider`: Real LLM summary generation
  - `SummaryProvider`: Factory class

### 2. API Routes (Backend)

Located in `backend/api_routes.py`:

```python
POST /api/v1/transcribe
  Request: { audio_path, model_size, language }
  Response: { success, transcript, segments, provider, is_fallback, error, processing_time_ms }

POST /api/v1/summarize
  Request: { transcript, template_name, template_sections, template_prompt }
  Response: { success, summary, provider, is_fallback, error, processing_time_ms }

GET /api/v1/providers/info
  Response: { transcription: {...}, summary: {...} }

GET /api/v1/health
  Response: { status, transcription_fallback, summary_fallback }
```

### 3. API Client (Frontend)

Located in `src/services/apiClient.ts`:

```typescript
class ApiClient {
  private baseUrl: string;
  async get<T>(endpoint: string): Promise<ApiResponse<T>>;
  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>>;
  async postFile<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>>;
}
```

### 4. Updated Services (Frontend)

- **transcriptionService.ts**: Now calls backend APIs with fallback
- **summaryGenerationService.ts**: Now calls backend APIs with fallback

## Configuration

### Backend (.env)

```bash
# Server
PORT=8000

# AI Providers
LLM_PROVIDER=ollama
ASR_PROVIDER=whisper

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:7b

# ASR
WHISPER_MODEL_SIZE=base
WHISPER_LANGUAGE=zh

# Feature Flags
ENABLE_REAL_ASR=false
ENABLE_REAL_LLM=false
```

### Frontend (.env)

```bash
# API Base URL (uses Vite proxy in dev)
VITE_API_BASE_URL=/api

# Feature Flags
VITE_ENABLE_TEMPLATES=true
VITE_ENABLE_EXPORT=true
```

### Vite Proxy (vite.config.ts)

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

## Security Benefits

1. **No API Keys in Frontend**: All sensitive credentials stay server-side
2. **Centralized Configuration**: Single source of truth for AI service settings
3. **Provider Abstraction**: Frontend doesn't need to know which AI services are used
4. **Easy Provider Switching**: Change provider in backend without touching frontend
5. **Graceful Degradation**: Automatic fallback when services are unavailable

## Error Handling & Fallback

Both services implement automatic fallback:

### Transcription Flow

1. Try backend Whisper ASR
2. If unavailable → use fallback mock transcription
3. Frontend displays provider status (backend vs fallback)

### Summary Flow

1. Try backend LLM provider
2. If unavailable → use fallback template-based summary
3. Frontend displays provider status (backend vs fallback)

## Testing

### Manual Testing

1. Start backend: `cd backend && python -m uvicorn main:app --reload --port 8000`
2. Start frontend: `cd web_backend/react-ui && npm run dev`
3. Check provider status: `curl http://localhost:8000/api/v1/providers/info`
4. Upload and process a meeting

### Expected Results

- Without API keys: Services use fallback mode
- With API keys configured: Services use real AI providers
- Frontend shows provider status hints

## Monitoring

Check provider availability:

```bash
# Backend health check
curl http://localhost:8000/api/v1/health

# Provider information
curl http://localhost:8000/api/v1/providers/info
```

Response example:

```json
{
  "transcription": {
    "type": "fallback",
    "available": true,
    "config": {}
  },
  "summary": {
    "type": "fallback",
    "available": true,
    "config": {}
  }
}
```

## Future Enhancements

1. Add more transcription providers (Azure, Google Cloud)
2. Add more LLM providers (Claude, Gemini)
3. Implement caching for repeated requests
4. Add request rate limiting
5. Add authentication/authorization
6. Implement request queuing for large files
7. Add metrics and monitoring

## Troubleshooting

### Backend won't start

- Check if port 8000 is available
- Verify dependencies: `pip install -r backend/requirements.txt`
- Check .env file exists and is valid

### Frontend can't reach backend

- Verify backend is running on port 8000
- Check Vite proxy configuration
- Check CORS settings in backend

### Fallback mode always active

- Verify API keys in .env
- Check `ENABLE_REAL_ASR` and `ENABLE_REAL_LLM` flags
- Check backend logs for provider initialization errors

## Migration Notes

This implementation is backward compatible:

- Existing frontend code continues to work
- Services automatically detect backend availability
- No database migration needed
- Can deploy incrementally
