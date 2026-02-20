"""ATLAS AGI Layer - Goal planning and proactive intelligence."""
from .planner import GoalPlanner, Goal, TaskStatus, TaskPriority
from .proactive import ProactiveEngine, create_default_engine

__all__ = [
    "GoalPlanner", "Goal", "TaskStatus", "TaskPriority",
    "ProactiveEngine", "create_default_engine"
]
