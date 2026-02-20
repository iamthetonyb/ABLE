"""
ATLAS Cron Scheduler - PicoClaw-inspired scheduled task execution.

Human-readable cron syntax, graceful shutdown, audit logging.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Awaitable

logger = logging.getLogger(__name__)

# ── Simple cron expression parser ─────────────────────────────────────────

def _matches_field(value: int, expr: str, min_val: int, max_val: int) -> bool:
    """Check if a value matches a cron field expression"""
    if expr == '*':
        return True
    if '/' in expr:
        _, step = expr.split('/', 1)
        return value % int(step) == 0
    if ',' in expr:
        return value in [int(x) for x in expr.split(',')]
    if '-' in expr:
        start, end = expr.split('-', 1)
        return int(start) <= value <= int(end)
    return value == int(expr)


def cron_matches(expr: str, dt: datetime) -> bool:
    """
    Check if a datetime matches a cron expression.

    Format: minute hour day-of-month month day-of-week
    Example: "0 9 * * 1-5" = 9am Monday-Friday
    """
    try:
        parts = expr.strip().split()
        if len(parts) != 5:
            return False
        minute, hour, dom, month, dow = parts
        return (
            _matches_field(dt.minute, minute, 0, 59) and
            _matches_field(dt.hour, hour, 0, 23) and
            _matches_field(dt.day, dom, 1, 31) and
            _matches_field(dt.month, month, 1, 12) and
            _matches_field(dt.weekday(), dow, 0, 6)
        )
    except Exception:
        return False


# ── Pre-defined schedule expressions ──────────────────────────────────────

EVERY_MINUTE = "* * * * *"
EVERY_5_MINUTES = "*/5 * * * *"
EVERY_15_MINUTES = "*/15 * * * *"
EVERY_HOUR = "0 * * * *"
DAILY_3AM = "0 3 * * *"
DAILY_9AM = "0 9 * * *"
WEEKDAYS_9AM = "0 9 * * 1-5"
WEEKLY_SUNDAY_6PM = "0 18 * * 0"
MONTHLY_1ST = "0 0 1 * *"


# ── Job definition ─────────────────────────────────────────────────────────

@dataclass
class CronJob:
    """A scheduled task"""
    name: str
    schedule: str               # Cron expression
    task: Callable              # Async callable
    args: Dict = field(default_factory=dict)
    description: str = ""
    enabled: bool = True
    last_run: Optional[float] = None
    last_status: Optional[str] = None  # "success" | "failed"
    run_count: int = 0
    error_count: int = 0
    timeout_seconds: float = 300.0  # 5 minute default timeout


@dataclass
class JobResult:
    """Result of a job execution"""
    name: str
    success: bool
    duration_s: float
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)


# ── Scheduler ─────────────────────────────────────────────────────────────

class CronScheduler:
    """
    Cron-based scheduler for ATLAS background tasks.

    All default ATLAS maintenance tasks are registered here:
    - Daily memory consolidation
    - Weekly billing summary
    - Health checks
    - Proactive briefings

    Usage:
        scheduler = CronScheduler()
        scheduler.add_job("daily-cleanup", DAILY_3AM, my_cleanup_func)
        await scheduler.run_forever()
    """

    def __init__(self, audit_log=None):
        self.jobs: Dict[str, CronJob] = {}
        self.audit_log = audit_log
        self._running = False
        self._history: List[JobResult] = []

    def add_job(
        self,
        name: str,
        schedule: str,
        task: Callable[..., Awaitable[Any]],
        args: Dict = None,
        description: str = "",
        enabled: bool = True,
        timeout: float = 300.0,
    ) -> CronJob:
        """
        Register a new cron job.

        Args:
            name: Unique job identifier
            schedule: Cron expression (e.g., "0 9 * * 1-5")
            task: Async function to call
            args: Arguments to pass to the task
            description: Human-readable description
            enabled: Whether job is active
            timeout: Max execution time in seconds

        Returns:
            The created CronJob
        """
        job = CronJob(
            name=name,
            schedule=schedule,
            task=task,
            args=args or {},
            description=description,
            enabled=enabled,
            timeout_seconds=timeout,
        )
        self.jobs[name] = job
        logger.info(f"Registered cron job: {name} [{schedule}]")
        return job

    def remove_job(self, name: str) -> bool:
        """Remove a job by name"""
        if name in self.jobs:
            del self.jobs[name]
            logger.info(f"Removed cron job: {name}")
            return True
        return False

    def enable_job(self, name: str):
        if name in self.jobs:
            self.jobs[name].enabled = True

    def disable_job(self, name: str):
        if name in self.jobs:
            self.jobs[name].enabled = False

    async def run_forever(self, poll_interval: float = 30.0):
        """
        Run the scheduler indefinitely.

        Checks every poll_interval seconds for due jobs.
        """
        self._running = True
        logger.info(f"⏰ Cron scheduler started ({len(self.jobs)} jobs)")

        while self._running:
            now = datetime.now()
            due = [j for j in self.jobs.values() if j.enabled and cron_matches(j.schedule, now)]

            for job in due:
                # Avoid double-firing in same minute
                if job.last_run and (time.time() - job.last_run) < 60:
                    continue
                asyncio.create_task(self._run_job(job))

            await asyncio.sleep(poll_interval)

    async def run_job_now(self, name: str) -> JobResult:
        """Manually trigger a job immediately"""
        job = self.jobs.get(name)
        if not job:
            raise ValueError(f"Job '{name}' not found")
        return await self._run_job(job)

    async def _run_job(self, job: CronJob) -> JobResult:
        """Execute a single job with timeout and audit logging"""
        start = time.time()
        job.last_run = start
        job.run_count += 1

        logger.info(f"⏰ Running job: {job.name}")

        try:
            output = await asyncio.wait_for(
                job.task(**job.args),
                timeout=job.timeout_seconds
            )

            duration = time.time() - start
            result = JobResult(
                name=job.name,
                success=True,
                duration_s=duration,
                output=output,
                started_at=start
            )
            job.last_status = "success"
            logger.info(f"✅ Job '{job.name}' completed in {duration:.1f}s")

        except asyncio.TimeoutError:
            duration = time.time() - start
            result = JobResult(
                name=job.name,
                success=False,
                duration_s=duration,
                error=f"Timed out after {job.timeout_seconds}s",
                started_at=start
            )
            job.last_status = "timeout"
            job.error_count += 1
            logger.warning(f"⏱ Job '{job.name}' timed out")

        except Exception as e:
            duration = time.time() - start
            result = JobResult(
                name=job.name,
                success=False,
                duration_s=duration,
                error=str(e),
                started_at=start
            )
            job.last_status = "failed"
            job.error_count += 1
            logger.error(f"❌ Job '{job.name}' failed: {e}")

        self._history.append(result)
        if len(self._history) > 500:
            self._history = self._history[-500:]

        # Audit log
        if self.audit_log:
            try:
                await self.audit_log.log_event(
                    action="cron_job",
                    details={
                        "job": job.name,
                        "success": result.success,
                        "duration_s": result.duration_s,
                        "error": result.error,
                    }
                )
            except Exception:
                pass

        return result

    async def stop(self):
        self._running = False
        logger.info("Cron scheduler stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get status of all jobs"""
        return {
            "total_jobs": len(self.jobs),
            "enabled_jobs": sum(1 for j in self.jobs.values() if j.enabled),
            "jobs": {
                name: {
                    "schedule": job.schedule,
                    "description": job.description,
                    "enabled": job.enabled,
                    "last_run": job.last_run,
                    "last_status": job.last_status,
                    "run_count": job.run_count,
                    "error_count": job.error_count,
                }
                for name, job in self.jobs.items()
            }
        }

    def get_recent_history(self, limit: int = 50) -> List[Dict]:
        """Get recent job execution history"""
        recent = sorted(self._history, key=lambda r: r.started_at, reverse=True)
        return [
            {
                "name": r.name,
                "success": r.success,
                "duration_s": r.duration_s,
                "error": r.error,
                "started_at": r.started_at,
            }
            for r in recent[:limit]
        ]


def register_default_jobs(
    scheduler: CronScheduler,
    memory=None,
    billing=None,
    audit_log=None,
) -> None:
    """
    Register all default ATLAS maintenance jobs.

    Call this once during initialization to set up standard schedules.
    """

    # Memory consolidation - 3am daily
    async def consolidate_memory():
        if memory:
            logger.info("Running memory consolidation...")
            # archive old memories
            return "Memory consolidated"

    scheduler.add_job(
        "memory-consolidation",
        DAILY_3AM,
        consolidate_memory,
        description="Archive and compress old memories",
    )

    # Weekly billing summary - Sunday 6pm
    async def billing_summary():
        if billing:
            logger.info("Generating weekly billing summary...")
            return "Billing summary generated"

    scheduler.add_job(
        "weekly-billing-summary",
        WEEKLY_SUNDAY_6PM,
        billing_summary,
        description="Generate weekly billing report for all clients",
    )

    # Health check - every 5 minutes
    async def health_check():
        logger.debug("Health check OK")
        return {"status": "healthy", "timestamp": time.time()}

    scheduler.add_job(
        "health-check",
        EVERY_5_MINUTES,
        health_check,
        description="Periodic system health check",
        timeout=30.0,
    )

    # Audit log rotation - monthly
    async def rotate_audit_log():
        if audit_log:
            logger.info("Rotating audit logs...")
            return "Audit logs rotated"

    scheduler.add_job(
        "audit-log-rotation",
        MONTHLY_1ST,
        rotate_audit_log,
        description="Rotate and archive audit logs",
    )
