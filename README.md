# ATLAS — Autonomous Task & Learning Agent System

An executive-level AI agent operating via Telegram with a secure multi-agent pipeline, persistent memory, billing tracking, and AGI-oriented features.

---

## Quick Start

### Option A — Docker (Recommended for production)

```bash
cd atlas
cp .env.example .env
# Edit .env with your credentials (see Configuration below)
docker-compose up -d
docker logs -f atlas
```

### Option B — Local Python

```bash
cd atlas
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python start.py
```

---

## Configuration

Edit `atlas/.env` with these required values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
ATLAS_OWNER_TELEGRAM_ID=your_telegram_user_id
OLLAMA_API_KEY=your_ollama_key          # Optional
NVIDIA_API_KEY=your_nvidia_key          # Optional (free tier AI)
ANTHROPIC_API_KEY=your_claude_key       # Optional (premium reasoning)
```

**Never commit `.env` to git** — it's in `.gitignore`.

---

## Architecture

```
AIDE/
├── atlas/              ← Main application
│   ├── start.py        ← Entry point
│   ├── core/           ← Agent pipeline, security, swarm orchestrator
│   ├── channels/       ← Telegram, Discord, Slack adapters
│   ├── memory/         ← Hybrid SQLite + vector + markdown memory
│   ├── skills/         ← Skill library, loader, and executor
│   │   └── scripts/    ← init_skill.py, package_skill.py
│   ├── tools/          ← Browser, shell, search, webhooks, MCP bridge
│   ├── billing/        ← Usage tracking and invoices
│   ├── scheduler/      ← Cron-based scheduled tasks
│   ├── security/       ← AES-256 encryption, malware scanner, secret isolation
│   └── audit/          ← Audit logs, alerts, traces, git trail
│
├── docs/               ← Documentation
│   ├── CUSTOMIZATION.md
│   ├── SECURITY.md
│   └── TOOLS.md
│
├── scripts/            ← Setup scripts
│   └── atlas-setup.sh
│
├── ATLAS.md            ← Full system configuration (1400+ lines)
└── SOUL.md             ← Core identity and behavioral directives
```

### Message Pipeline

```
Telegram → UnifiedGateway → Scanner → Auditor → TrustGate → Executor → AI Backend → Response
```

### AI Provider Chain

```
1. NVIDIA NIM (kimi-k2.5 / Qwen3.5)  → Free tier
2. OpenRouter (kimi-k2.5)            → Fallback ($0.60/$3.00 per M)
3. Anthropic (claude-opus-4-5)       → Complex reasoning ($5/$25 per M)
4. Ollama (qwen3.5 / llama)          → Offline fallback (free)
```

### Agent Swarm

Complex tasks (complexity score ≥ 0.6) auto-spawn agent swarms:
- RESEARCHER, ANALYST, WRITER, CODER, REVIEWER, CRITIC, PLANNER, EXECUTOR, COORDINATOR

---

## Server Deployment (Digital Ocean)

From your local machine:

```bash
bash deploy-to-server.sh
```

Or GitHub Actions auto-deploys on push to main.

Manual steps:
```bash
ssh root@YOUR_SERVER_IP
git clone https://github.com/iamthetonyb/AIDE.git /opt/atlas/AIDE
cd /opt/atlas/AIDE/atlas
cp .env.example .env && nano .env
docker-compose up -d
docker logs -f atlas
```

---

## Health Check

Once running, verify:
- `curl http://localhost:8080/health` → `{"status": "ok"}`
- Send `/start` to your Telegram bot

---

## Key Files

| File | Purpose |
|------|---------|
| `ATLAS.md` | Full system configuration — read every session |
| `SOUL.md` | Core identity and behavioral directives |
| `docs/CUSTOMIZATION.md` | Personalization guide |
| `atlas/config/gateway.json` | Non-secret runtime settings |
| `atlas/.env` | Secrets (never commit) |

---

## Skill System

Create new skills:
```bash
python atlas/skills/scripts/init_skill.py my-skill --path atlas/skills/library --resources scripts,references
```

Package skills:
```bash
python atlas/skills/scripts/package_skill.py atlas/skills/library/my-skill
```

Install from skills.sh registry:
```bash
npx skills add <owner/repo>
```

---

## Qwen 3.5 Optimizations

When using Qwen 3.5 via Ollama:
- **YaRN context extension**: 32K → 262K → 1M tokens
- **Thinking modes**: off / low / medium / high / ultra
- **MoE routing**: 235B total params, 22B active per forward pass

See `atlas/core/providers/ollama.py` for `QwenConfig`.
