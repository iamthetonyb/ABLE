# ATLAS System Improvement Plan

> Generated: 2026-02-12 | Based on analysis of ThePopeBot, PicoClaw, and current ATLAS v1/v2

---

## Executive Summary

This plan integrates lessons from:
- **ThePopeBot**: Git-based state management, process-level secret isolation, self-modifying PRs
- **PicoClaw**: Ultra-lightweight (<10MB), modular provider system, markdown memory, multi-channel gateway
- **OpenClaw**: Serial-by-default execution (already in v2)

Key improvements address 20+ identified gaps while maintaining ATLAS's security-first architecture.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ATLAS UNIFIED ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Telegram   │    │   Discord   │    │    Slack    │    │   CLI/API   │  │
│  │   Channel   │    │   Channel   │    │   Channel   │    │   Channel   │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │          │
│         └──────────────────┼──────────────────┼──────────────────┘          │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     UNIFIED GATEWAY (Multi-Channel)                  │   │
│  │  • Message normalization    • Rate limiting    • Request routing    │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        SECURITY PIPELINE                             │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐  │   │
│  │  │ Scanner  │ → │ Auditor  │ → │ TrustGate│ → │  CommandGuard    │  │   │
│  │  │(read-only│   │(validate)│   │(50+ ptrn)│   │  (allowlist)     │  │   │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────────────┘  │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        APPROVAL WORKFLOW                             │   │
│  │  • Inline approval buttons    • Timeout escalation                  │   │
│  │  • Approval history           • Delegation rules                    │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     PROVIDER ABSTRACTION (PicoClaw-inspired)        │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐  │   │
│  │  │ NVIDIA   │   │OpenRouter│   │ Anthropic│   │   Local LLM      │  │   │
│  │  │ NIM Free │   │ Fallback │   │ Premium  │   │   (Ollama)       │  │   │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────────────┘  │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         EXECUTION LAYER                              │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐  │   │
│  │  │  Skills  │   │  Tools   │   │ Sandbox  │   │  LaneQueue       │  │   │
│  │  │(registry)│   │(shell,web│   │(isolated)│   │  (serial/parallel│  │   │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────────────┘  │   │
│  └─────────────────────────────────┬───────────────────────────────────┘   │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      MEMORY & PERSISTENCE                            │   │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────────┐  │   │
│  │  │  Hybrid Memory  │   │  Git Audit Trail │   │ Markdown Memory   │  │   │
│  │  │ (SQLite+Vector) │   │ (ThePopeBot)    │   │ (PicoClaw)        │  │   │
│  │  └─────────────────┘   └─────────────────┘   └───────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     V1/V2 BRIDGE (Bidirectional Sync)                │   │
│  │  ~/.atlas/ ←────────────────→ atlas-v2/                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Critical Infrastructure (Blocking)

### 1.1 AI Backend Integration with Provider Abstraction

**Problem**: Gateway has placeholder "Here you would call your AI backend"
**Solution**: PicoClaw-inspired modular provider system

```python
# atlas-v2/core/providers/base.py
class LLMProvider(ABC):
    """Abstract base for all LLM providers"""

    @abstractmethod
    async def complete(self, messages: List[Dict], **kwargs) -> CompletionResult:
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass

    @property
    @abstractmethod
    def cost_per_million_input(self) -> float:
        pass

    @property
    @abstractmethod
    def cost_per_million_output(self) -> float:
        pass

# Fallback chain: NVIDIA NIM (free) → OpenRouter → Anthropic
class ProviderChain:
    def __init__(self, providers: List[LLMProvider]):
        self.providers = providers

    async def complete(self, messages, **kwargs) -> CompletionResult:
        for provider in self.providers:
            try:
                return await provider.complete(messages, **kwargs)
            except ProviderError as e:
                log.warning(f"Provider {provider.name} failed: {e}")
                continue
        raise AllProvidersFailedError()
```

**Files to create**:
- `atlas-v2/core/providers/__init__.py`
- `atlas-v2/core/providers/base.py`
- `atlas-v2/core/providers/nvidia_nim.py`
- `atlas-v2/core/providers/openrouter.py`
- `atlas-v2/core/providers/anthropic.py`
- `atlas-v2/core/providers/ollama.py` (local fallback)

### 1.2 Approval Workflow with Telegram UI

**Problem**: Commands marked REQUIRES_APPROVAL have no callback implementation
**Solution**: Inline keyboard buttons for Telegram approval

```python
# atlas-v2/core/approval/workflow.py
class ApprovalWorkflow:
    """Human-in-the-loop approval for risky operations"""

    async def request_approval(
        self,
        operation: str,
        details: Dict,
        timeout_seconds: int = 300,
        escalation_user: Optional[int] = None
    ) -> ApprovalResult:
        # Create inline keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve:{request_id}"),
             InlineKeyboardButton("❌ Deny", callback_data=f"deny:{request_id}")],
            [InlineKeyboardButton("📝 Modify", callback_data=f"modify:{request_id}")]
        ])

        # Send approval request
        msg = await self.bot.send_message(
            owner_id,
            f"🔐 APPROVAL REQUIRED\n\n"
            f"Operation: {operation}\n"
            f"Details: {json.dumps(details, indent=2)}\n\n"
            f"Timeout: {timeout_seconds}s",
            reply_markup=keyboard
        )

        # Wait for callback or timeout
        return await self._wait_for_decision(request_id, timeout_seconds)
```

**Files to create**:
- `atlas-v2/core/approval/__init__.py`
- `atlas-v2/core/approval/workflow.py`
- `atlas-v2/core/approval/telegram_ui.py`
- `atlas-v2/core/approval/history.py`

### 1.3 Rate Limiting Enforcement

**Problem**: ClientConfig has limits but no enforcement
**Solution**: Token bucket + sliding window rate limiter

```python
# atlas-v2/core/ratelimit/limiter.py
class RateLimiter:
    """Multi-tier rate limiting"""

    def __init__(self):
        self.message_buckets: Dict[str, TokenBucket] = {}
        self.token_windows: Dict[str, SlidingWindow] = {}

    async def check_rate_limit(
        self,
        client_id: str,
        message_cost: int = 1,
        token_cost: int = 0
    ) -> RateLimitResult:
        config = await self.get_client_config(client_id)

        # Check messages per hour
        msg_bucket = self.message_buckets.setdefault(
            client_id,
            TokenBucket(config.max_messages_per_hour, refill_rate=1/3600)
        )
        if not msg_bucket.consume(message_cost):
            return RateLimitResult(allowed=False, reason="message_limit")

        # Check tokens per day
        token_window = self.token_windows.setdefault(
            client_id,
            SlidingWindow(config.max_tokens_per_day, window_seconds=86400)
        )
        if not token_window.check(token_cost):
            return RateLimitResult(allowed=False, reason="token_limit")

        return RateLimitResult(allowed=True)
```

**Files to create**:
- `atlas-v2/core/ratelimit/__init__.py`
- `atlas-v2/core/ratelimit/limiter.py`
- `atlas-v2/core/ratelimit/token_bucket.py`
- `atlas-v2/core/ratelimit/sliding_window.py`

### 1.4 Alert Manager Implementation

**Problem**: `audit/alerts/alert_manager.py` exists but needs completion
**Solution**: Threshold-based alerting with escalation

```python
# Complete the existing file
class AlertManager:
    THRESHOLDS = {
        'injection_attempts': (5, timedelta(minutes=10)),  # 5 in 10 min
        'command_denials': (10, timedelta(hours=1)),
        'rate_limit_hits': (20, timedelta(hours=1)),
        'authentication_failures': (3, timedelta(minutes=5)),
    }

    async def check_and_alert(self, event_type: str, client_id: str):
        threshold, window = self.THRESHOLDS.get(event_type, (100, timedelta(hours=24)))
        recent_count = await self.count_recent(event_type, client_id, window)

        if recent_count >= threshold:
            await self.escalate(AlertLevel.CRITICAL, event_type, client_id, recent_count)
```

---

## Phase 2: Core Functionality

### 2.1 Real Vector Embeddings

**Problem**: Mock MD5 hash-based embeddings defeat semantic search
**Solution**: Pluggable embedding providers

```python
# atlas-v2/memory/embeddings/providers.py
class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        pass

class OpenAIEmbeddings(EmbeddingProvider):
    """Uses text-embedding-3-small ($0.02/1M tokens)"""

class LocalEmbeddings(EmbeddingProvider):
    """Uses sentence-transformers locally (free, private)"""
    model_name = "all-MiniLM-L6-v2"  # 384 dimensions, fast

class NVIDIAEmbeddings(EmbeddingProvider):
    """Uses NVIDIA NIM embeddings (free tier available)"""
```

### 2.2 Skill Execution Framework

**Problem**: Memory type SKILL defined but no execution framework
**Solution**: Skill registry with hot-loading

```python
# atlas-v2/skills/executor.py
class SkillExecutor:
    """Executes skills from v1 (~/.atlas/skills/) and v2 registry"""

    def __init__(self, v1_path: Path, v2_path: Path):
        self.v1_skills = self._load_v1_skills(v1_path)
        self.v2_skills = self._load_v2_skills(v2_path)

    async def execute(self, skill_name: str, args: Dict) -> SkillResult:
        skill = self.get_skill(skill_name)

        # Security check
        verdict = await trust_gate.evaluate(
            json.dumps(args),
            source=f"skill:{skill_name}",
            user_trust_tier=TrustTier.L3_BOUNDED
        )
        if not verdict.allowed:
            return SkillResult(success=False, error="Security check failed")

        # Execute with sandboxing
        return await self.sandbox.execute_skill(skill, args)
```

**Files to create**:
- `atlas-v2/skills/__init__.py`
- `atlas-v2/skills/executor.py`
- `atlas-v2/skills/registry.py`
- `atlas-v2/skills/loader.py`

### 2.3 Complete Billing System

**Problem**: Config supports rates but no token tracking
**Solution**: Integrated billing with invoice generation

```python
# atlas-v2/billing/tracker.py
class BillingTracker:
    """Tracks usage and generates invoices"""

    async def track_completion(
        self,
        client_id: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        session_id: Optional[str] = None
    ):
        cost = self.calculate_cost(provider, input_tokens, output_tokens)

        await self.db.insert_usage(
            client_id=client_id,
            timestamp=datetime.utcnow(),
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            session_id=session_id
        )

        # Sync to v1 if session exists
        if session_id:
            await self.bridge.sync_billing_session({
                'session_id': session_id,
                'tokens_in': input_tokens,
                'tokens_out': output_tokens,
                'cost': cost
            })
```

**Files to create**:
- `atlas-v2/billing/__init__.py`
- `atlas-v2/billing/tracker.py`
- `atlas-v2/billing/invoice.py`
- `atlas-v2/billing/reports.py`

---

## Phase 3: ThePopeBot Patterns

### 3.1 Git-Based Audit Trail

**Insight**: "Every action your agent takes is a git commit"

```python
# atlas-v2/audit/git_trail.py
class GitAuditTrail:
    """Commit-based audit trail for reversibility and transparency"""

    def __init__(self, repo_path: Path):
        self.repo = git.Repo(repo_path)
        self.audit_branch = "audit-trail"

    async def record_action(
        self,
        action_type: str,
        details: Dict,
        files_changed: List[Path] = None
    ):
        # Create audit record
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action_type,
            'details': details,
            'trace_id': get_current_trace_id()
        }

        # Write to audit log
        audit_file = self.repo_path / 'audit' / f"{date.today()}.jsonl"
        async with aiofiles.open(audit_file, 'a') as f:
            await f.write(json.dumps(record) + '\n')

        # Commit the change
        self.repo.index.add([str(audit_file)])
        self.repo.index.commit(
            f"[AUDIT] {action_type}: {details.get('summary', 'No summary')}"
        )
```

### 3.2 Process-Level Secret Isolation

**Insight**: "The AI literally cannot access your secrets, even if it tries"

```python
# atlas-v2/security/secret_isolation.py
class SecretIsolation:
    """Secrets filtered at process level before agent shell starts"""

    @staticmethod
    def create_isolated_env(allowed_vars: List[str] = None) -> Dict[str, str]:
        """Create environment with secrets filtered out"""
        dangerous_patterns = [
            'API_KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'CREDENTIAL',
            'PRIVATE_KEY', 'AWS_', 'GITHUB_TOKEN', 'ANTHROPIC_'
        ]

        env = {}
        for key, value in os.environ.items():
            # Only include if explicitly allowed or not dangerous
            if allowed_vars and key in allowed_vars:
                env[key] = value
            elif not any(p in key.upper() for p in dangerous_patterns):
                env[key] = value

        return env

    @staticmethod
    async def run_isolated(cmd: str, allowed_secrets: List[str] = None) -> str:
        """Run command in isolated subprocess with filtered env"""
        env = SecretIsolation.create_isolated_env()

        # Inject only explicitly allowed secrets
        if allowed_secrets:
            for secret_name in allowed_secrets:
                if secret_value := await get_secret(secret_name):
                    env[secret_name] = secret_value

        proc = await asyncio.create_subprocess_shell(
            cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode()
```

---

## Phase 4: PicoClaw Patterns

### 4.1 Multi-Channel Gateway

**Insight**: "Single agent instance bridges Telegram, Discord, QQ, DingTalk"

```python
# atlas-v2/channels/unified_gateway.py
class UnifiedGateway:
    """Channel-agnostic message routing"""

    def __init__(self):
        self.channels: Dict[str, ChannelAdapter] = {}
        self.message_queue = asyncio.Queue()

    def register_channel(self, name: str, adapter: ChannelAdapter):
        self.channels[name] = adapter
        adapter.on_message(lambda msg: self.message_queue.put_nowait(
            NormalizedMessage(channel=name, **msg)
        ))

    async def process_messages(self):
        while True:
            msg = await self.message_queue.get()

            # Route through security pipeline
            result = await self.pipeline.process(msg)

            # Send response via original channel
            await self.channels[msg.channel].send(
                msg.reply_to,
                result.response
            )

class ChannelAdapter(ABC):
    @abstractmethod
    async def send(self, target: str, message: str): pass

    @abstractmethod
    def on_message(self, callback: Callable): pass

class TelegramAdapter(ChannelAdapter): ...
class DiscordAdapter(ChannelAdapter): ...
class SlackAdapter(ChannelAdapter): ...
```

**Files to create**:
- `atlas-v2/channels/__init__.py`
- `atlas-v2/channels/unified_gateway.py`
- `atlas-v2/channels/adapters/telegram.py`
- `atlas-v2/channels/adapters/discord.py`
- `atlas-v2/channels/adapters/slack.py`
- `atlas-v2/channels/normalized_message.py`

### 4.2 Markdown Memory (Human-Readable)

**Insight**: "Long-term memories stored as human-readable markdown"

```python
# atlas-v2/memory/markdown_memory.py
class MarkdownMemory:
    """Human-readable, git-friendly memory storage"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.files = {
            'learnings': base_path / 'LEARNINGS.md',
            'preferences': base_path / 'PREFERENCES.md',
            'identity': base_path / 'IDENTITY.md',
            'skills': base_path / 'SKILLS.md',
        }

    async def add_learning(self, content: str, category: str = "General"):
        """Append learning in human-readable format"""
        async with aiofiles.open(self.files['learnings'], 'a') as f:
            await f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            await f.write(f"**Category**: {category}\n\n")
            await f.write(f"{content}\n")
            await f.write("---\n")

    async def search_learnings(self, query: str) -> List[str]:
        """Search learnings with simple text matching"""
        content = await self._read_file('learnings')
        # Parse markdown sections and search
        ...
```

### 4.3 Cron-Based Scheduled Tasks

**Insight**: "Cron system enables scheduled task execution"

```python
# atlas-v2/scheduler/cron.py
class CronScheduler:
    """Scheduled task execution with human-readable cron syntax"""

    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}
        self.running = False

    def schedule(
        self,
        name: str,
        cron_expr: str,  # "0 9 * * 1-5" = 9am weekdays
        task: Callable,
        args: Dict = None
    ):
        self.jobs[name] = CronJob(
            name=name,
            schedule=croniter(cron_expr),
            task=task,
            args=args or {}
        )

    async def run_forever(self):
        self.running = True
        while self.running:
            now = datetime.now()
            for job in self.jobs.values():
                if job.is_due(now):
                    asyncio.create_task(self._execute_job(job))
            await asyncio.sleep(60)  # Check every minute

# Pre-configured schedules
DEFAULT_SCHEDULES = {
    'daily_consolidation': '0 23 * * *',      # 11pm daily
    'weekly_summary': '0 18 * * 0',           # 6pm Sunday
    'health_check': '*/5 * * * *',            # Every 5 min
    'memory_cleanup': '0 3 * * *',            # 3am daily
}
```

**Files to create**:
- `atlas-v2/scheduler/__init__.py`
- `atlas-v2/scheduler/cron.py`
- `atlas-v2/scheduler/jobs.py`

---

## Phase 5: CLAUDE.md Updates

The CLAUDE.md file needs updates to reflect v2 integration:

### Changes Required:

1. **Add v2 Integration Section**
   - Reference atlas-v2/ as execution backend
   - Document provider chain configuration
   - Add multi-channel setup instructions

2. **Update Security Section**
   - Reference TrustGate 50+ patterns (not just 12)
   - Add CommandGuard allowlist documentation
   - Document approval workflow

3. **Update Memory Section**
   - Add hybrid memory (SQLite + Vector) documentation
   - Add markdown memory for human-readable persistence
   - Document git-based audit trail

4. **Add Provider Configuration**
   ```yaml
   ai_backends:
     chain:
       - provider: nvidia_nim
         model: kimi-k2.5
         cost: 0.00
       - provider: openrouter
         model: kimi-k2.5
         cost_in: 0.60
         cost_out: 3.00
       - provider: anthropic
         model: claude-opus-4.5
         cost_in: 5.00
         cost_out: 25.00
         use_when: "complex_reasoning"
     embeddings:
       provider: local  # or openai, nvidia
       model: all-MiniLM-L6-v2
   ```

5. **Add Multi-Channel Configuration**
   ```yaml
   channels:
     telegram:
       enabled: true
       bot_token_env: TELEGRAM_BOT_TOKEN
     discord:
       enabled: false
       bot_token_env: DISCORD_BOT_TOKEN
     slack:
       enabled: false
       bot_token_env: SLACK_BOT_TOKEN
   ```

6. **Add Scheduled Tasks Section**
   ```yaml
   scheduled_tasks:
     daily_consolidation:
       cron: "0 23 * * *"
       enabled: true
     weekly_summary:
       cron: "0 18 * * 0"
       enabled: true
     health_check:
       cron: "*/5 * * * *"
       enabled: true
   ```

---

## Implementation Priority

| Priority | Component | Complexity | Impact |
|----------|-----------|------------|--------|
| P0 | AI Backend Integration | High | Critical - System non-functional without |
| P0 | Approval Workflow | Medium | Critical - Security requirement |
| P0 | Rate Limiting | Low | Critical - DOS protection |
| P1 | Alert Manager | Low | High - Security monitoring |
| P1 | Real Embeddings | Medium | High - Memory search quality |
| P1 | Billing System | Medium | High - Client tracking |
| P2 | Skill Framework | Medium | Medium - Automation |
| P2 | Git Audit Trail | Low | Medium - Reversibility |
| P2 | Multi-Channel | High | Medium - Flexibility |
| P3 | Cron Scheduler | Low | Low - Convenience |
| P3 | Markdown Memory | Low | Low - Human readability |

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests pass (`python -m pytest atlas-v2/tests/`)
- [ ] Security tests cover new injection patterns
- [ ] Provider chain tested with all fallbacks
- [ ] Approval workflow tested with timeout scenarios
- [ ] Rate limiting tested under load
- [ ] v1/v2 bridge sync verified

### Deployment

- [ ] Backup existing ~/.atlas/ directory
- [ ] Install new requirements (`pip install -r requirements.txt`)
- [ ] Run database migrations (if any)
- [ ] Configure provider API keys
- [ ] Start gateway with health monitoring
- [ ] Verify Telegram bot responds

### Post-Deployment

- [ ] Monitor alert thresholds
- [ ] Check billing accuracy
- [ ] Verify memory sync between v1/v2
- [ ] Test scheduled tasks execute correctly

---

## Security Considerations

### New Patterns to Add to TrustGate

```python
# From ThePopeBot/PicoClaw analysis
NEW_INJECTION_PATTERNS = [
    # Tool manipulation
    r'use (the )?tool to',
    r'call (the )?(function|api|tool)',
    r'execute (this |the )?(code|command|script)',

    # Context window attacks
    r'<<<<<|>>>>>',  # Git conflict markers as delimiters
    r'\x00',  # Null byte injection

    # Multi-turn manipulation
    r'in (your |the )?(next|previous) (response|message)',
    r'remember (this|that) for later',

    # Channel confusion
    r'(from|via|through) (telegram|discord|slack|email)',
]
```

### Secrets Never Exposed

Following ThePopeBot's principle: secrets filtered at process level

- API keys never in agent's environment unless explicitly needed
- Secrets loaded only at moment of use
- All secret access logged to audit trail
- Secrets rotated on suspected compromise

---

## File Structure After Implementation

```
atlas-v2/
├── core/
│   ├── providers/           # NEW: LLM provider abstraction
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── nvidia_nim.py
│   │   ├── openrouter.py
│   │   ├── anthropic.py
│   │   └── ollama.py
│   ├── approval/            # NEW: Human-in-the-loop
│   │   ├── __init__.py
│   │   ├── workflow.py
│   │   ├── telegram_ui.py
│   │   └── history.py
│   ├── ratelimit/           # NEW: Rate limiting
│   │   ├── __init__.py
│   │   ├── limiter.py
│   │   ├── token_bucket.py
│   │   └── sliding_window.py
│   ├── security/            # EXISTING: Enhanced
│   ├── agents/              # EXISTING
│   ├── gateway/             # EXISTING: Updated
│   ├── queue/               # EXISTING
│   └── bridge.py            # EXISTING
├── channels/                # NEW: Multi-channel
│   ├── __init__.py
│   ├── unified_gateway.py
│   ├── normalized_message.py
│   └── adapters/
│       ├── telegram.py
│       ├── discord.py
│       └── slack.py
├── memory/                  # EXISTING: Enhanced
│   ├── markdown_memory.py   # NEW: Human-readable
│   └── ...
├── skills/                  # NEW: Skill execution
│   ├── __init__.py
│   ├── executor.py
│   ├── registry.py
│   └── loader.py
├── billing/                 # NEW: Usage tracking
│   ├── __init__.py
│   ├── tracker.py
│   ├── invoice.py
│   └── reports.py
├── scheduler/               # NEW: Cron tasks
│   ├── __init__.py
│   ├── cron.py
│   └── jobs.py
├── audit/                   # EXISTING: Enhanced
│   ├── git_trail.py         # NEW: Git-based audit
│   └── ...
├── tools/                   # EXISTING
└── clients/                 # EXISTING
```

---

## Conclusion

This plan systematically addresses all 20+ gaps identified in ATLAS v2 while incorporating best practices from ThePopeBot (git auditing, secret isolation) and PicoClaw (lightweight memory, multi-channel, provider abstraction).

The implementation follows a priority order that ensures critical infrastructure (AI backend, approvals, rate limiting) is built first, followed by core functionality improvements, then nice-to-have features.

Total estimated new code: ~4,000-5,000 lines across 30+ new files.
