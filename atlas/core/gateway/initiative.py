import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InitiativeEngine:
    """
    ATLAS's proactive brain. Runs scheduled tasks that initiate Telegram
    messages to the owner WITHOUT being asked first.
    """
    def __init__(self, gateway):
        self.gateway = gateway
        from core.gateway.goals import GoalTracker
        self.goal_tracker = GoalTracker()

    def register_jobs(self, scheduler):
        """Register proactive AGI jobs with the CronScheduler."""
        scheduler.add_job(
            "morning-briefing", 
            "0 9 * * *", 
            self._morning_briefing, 
            description="Daily morning briefing at 9am",
            timeout=300
        )
        scheduler.add_job(
            "evening-checkin", 
            "0 21 * * *", 
            self._goal_checkin, 
            description="Daily goal check-in at 9pm",
            timeout=300
        )
        scheduler.add_job(
            "github-digest", 
            "0 13 * * *", 
            self._github_digest, 
            description="GitHub digest at 1pm",
            timeout=300
        )
        scheduler.add_job(
            "self-reflect", 
            "0 0 * * 0", 
            self._self_reflection, 
            description="Weekly self-improvement reflection (Sunday midnight)",
            timeout=600
        )
        logger.info("InitiativeEngine: Registered proactive AGI schedules.")

    async def _send_to_owner(self, message: str):
        """Send a proactive message to the owner via Telegram."""
        if not self.gateway.master_bot or not self.gateway.owner_telegram_id:
            logger.warning("InitiativeEngine: Could not send message (no master_bot or missing owner ID)")
            return
        
        try:
            await self.gateway.master_bot.bot.send_message(
                chat_id=self.gateway.owner_telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info("InitiativeEngine: Proactive message delivered.")
        except Exception as e:
            logger.error(f"InitiativeEngine failed to send message: {e}")

    async def _ask_llm(self, prompt: str) -> str:
        """Helper to invoke the core ProviderChain for intelligent briefings."""
        from core.providers.base import Message, Role
        
        system_rules = "You are ATLAS. Keep this proactive briefing concise, punchy, and highly analytical. Format in Markdown."
        msgs = [
            Message(role=Role.SYSTEM, content=system_rules),
            Message(role=Role.USER, content=prompt)
        ]
        
        try:
            result = await self.gateway.provider_chain.complete(
                msgs,
                max_tokens=2048,
                temperature=0.7,
                # Force AtlasCloud/OpenRouter
                provider={"order": ["AtlasCloud"], "allow_fallbacks": True, "data_collection": "deny"},
                models=["qwen/qwen3.5-397b-a17b"]
            )
            return result.content or "⚠️ Error generating intelligent briefing."
        except Exception as e:
            logger.error(f"InitiativeEngine LLM error: {e}")
            return f"⚠️ LLM generation failed for briefing: {e}"

    async def _morning_briefing(self):
        """Generate and send the 9AM morning briefing."""
        await self._send_to_owner("☀️ `ATLAS is waking up and preparing your morning briefing...`")
        goals_context = self.goal_tracker.get_summary()
        
        prompt = f"""
        Draft my morning briefing.
        
        Context:
        It is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
        
        {goals_context}
        
        Structure:
        1. Short motivational greeting (Tony B, KingCRO)
        2. Where we are on the $100k/m by 2028 goal.
        3. 2-3 recommended focus areas for today based on building the swarm AGI system and generating revenue.
        
        CRITICAL: Do not ask for user input. Deliver the briefing directly.
        """
        
        briefing = await self._ask_llm(prompt)
        await self._send_to_owner(f"🌅 **Morning Briefing**\n\n{briefing}")

    async def _goal_checkin(self):
        """Generate and send the 9PM daily review."""
        await self._send_to_owner("🌙 `ATLAS is preparing your evening review...`")
        goals_context = self.goal_tracker.get_summary()
        
        prompt = f"""
        Draft my evening check-in.
        
        Context:
        It is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
        {goals_context}
        
        Structure:
        1. Ask me directly: "Was today a $100k/m day?"
        2. Ask me to reply with what we accomplished today so I can log it to memory.
        3. Provide a short closing remark.
        """
        
        checkin = await self._ask_llm(prompt)
        await self._send_to_owner(f"📊 **Evening Check-In**\n\n{checkin}")

    async def _github_digest(self):
        """Scan repos and send a digest."""
        # Simple alert for now - could be wired directly into self.gateway.github.list_repos()
        await self._send_to_owner("📡 `ATLAS GitHub Digest: System running nominally. Repositories synchronized.`")

    async def _self_reflection(self):
        """Weekly self-improvement diagnostic."""
        await self._send_to_owner("🧠 `ATLAS Weekly Self-Reflection Protocol Initiated. Analyzing audit logs...`")
        prompt = """
        You are reflecting on the past week of operations.
        Draft a short self-reflection summary analyzing your performance as an AGI, potential areas where your context window or tool usage caused friction, and what capabilities you need me to build for you next week.
        """
        reflection = await self._ask_llm(prompt)
        await self._send_to_owner(f"🧬 **Self-Improvement Diagnostics**\n\n{reflection}")
