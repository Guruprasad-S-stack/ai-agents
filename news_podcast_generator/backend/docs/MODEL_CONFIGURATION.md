# Model Configuration Summary

## ✅ Fixed Issues

### Main Orchestrator Agent
- **File**: `db/agent_config_v2.py`
- **Before**: `AGENT_MODEL = "gpt-4o"` ❌
- **After**: `AGENT_MODEL = "gemini-2.5-pro"` ✅
- **Used in**: `services/celery_tasks.py` (main agent orchestrator)
- **API Key**: `GOOGLE_API_KEY` ✅

---

## ✅ Correctly Configured Agents

### 1. Main Orchestrator (Podcast Agent)
- **File**: `services/celery_tasks.py`
- **Model**: `Gemini(id=AGENT_MODEL)` → `"gemini-2.5-pro"`
- **API Key**: `GOOGLE_API_KEY` ✅
- **Purpose**: Main agent that orchestrates the podcast creation workflow

### 2. Search Agent
- **File**: `agents/search_agent.py`
- **Model**: `Gemini(id="gemini-2.5-flash")`
- **API Key**: `GOOGLE_API_KEY` ✅
- **Purpose**: Searches for articles and sources

### 3. Scrape Agent
- **File**: `agents/scrape_agent.py`
- **Model**: `Gemini(id="gemini-2.5-flash")`
- **API Key**: `GOOGLE_API_KEY` ✅
- **Purpose**: Scrapes content from URLs

### 4. Script Agent
- **File**: `agents/script_agent.py`
- **Model**: `Gemini(id="gemini-2.5-pro")`
- **API Key**: `GOOGLE_API_KEY` ✅
- **Purpose**: Generates podcast scripts

---

## ✅ Intentionally Using OpenAI (Not Errors)

These are correctly using OpenAI models for specific tasks:

### Image Generation
- **Files**: 
  - `agents/image_generate_agent.py`
  - `tools/pipeline/image_generate_agent.py`
- **Model**: `OpenAIChat(id="gpt-4o")`
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: Image generation (DALL-E)

### Browser Search
- **File**: `tools/web_search.py`
- **Model**: `ChatOpenAI(model="gpt-4o")`
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: Browser automation with browser-use library

### Social Media Analysis
- **File**: `tools/social/x_agent.py`
- **Model**: `OpenAIChat(id="gpt-4o")`
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: X.com post analysis

### Pipeline Tools (Legacy/Alternative)
- **Files**: 
  - `tools/pipeline/search_agent.py`
  - `tools/pipeline/scrape_agent.py`
  - `tools/pipeline/script_agent.py`
- **Model**: `OpenAIChat(id="gpt-4o-mini")`
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: Alternative pipeline implementations

### Text-to-Speech
- **Files**: 
  - `utils/text_to_audio_openai.py`
  - `utils/tts_engine_selector.py`
- **Model**: `"gpt-4o-mini-tts"` (OpenAI TTS)
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: Text-to-speech generation

### Translation
- **File**: `utils/translate_podcast.py`
- **Model**: `"gpt-4o"`
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: Podcast translation

### Article Analysis
- **File**: `processors/ai_analysis_processor.py`
- **Model**: `"gpt-4o"`
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: Article content analysis

### Embeddings
- **Files**: 
  - `tools/embedding_search.py`
  - `processors/embedding_processor.py`
- **Model**: `"text-embedding-3-small"` (OpenAI)
- **API Key**: `OPENAI_API_KEY` ✅
- **Purpose**: Vector embeddings for search

---

## 📋 Required API Keys

### Essential
- `GOOGLE_API_KEY` - Required for main agent workflow (Gemini models)
- `ELEVENLABS_API_KEY` - Required for TTS (ElevenLabs)

### Optional (for specific features)
- `OPENAI_API_KEY` - For image generation, browser search, translations, embeddings

---

## ✅ Verification Checklist

- [x] Main orchestrator uses Gemini (`gemini-2.5-pro`)
- [x] Main orchestrator uses `GOOGLE_API_KEY`
- [x] Search agent uses Gemini (`gemini-2.5-flash`)
- [x] Scrape agent uses Gemini (`gemini-2.5-flash`)
- [x] Script agent uses Gemini (`gemini-2.5-pro`)
- [x] All Gemini agents use `GOOGLE_API_KEY`
- [x] OpenAI models use `OPENAI_API_KEY` (intentional)

---

## 🔧 Model Naming Convention

### Gemini Models
- `gemini-2.5-pro` - For complex tasks (orchestration, script generation)
- `gemini-2.5-flash` - For faster tasks (search, scraping)

### OpenAI Models
- `gpt-4o` - For complex tasks (image gen, analysis)
- `gpt-4o-mini` - For simpler tasks (pipeline tools)
- `gpt-4o-mini-tts` - For text-to-speech
- `text-embedding-3-small` - For embeddings

