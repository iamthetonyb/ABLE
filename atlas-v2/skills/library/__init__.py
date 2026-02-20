"""
Skills Library

Collection of specialized skills that can be triggered automatically or explicitly.
"""

from .copywriting import (
    CopywritingEngine,
    CopyBrief,
    AudienceProfile,
    get_copywriting_engine,
    should_trigger as copywriting_should_trigger,
    get_system_prompt as copywriting_system_prompt,
)

__all__ = [
    "CopywritingEngine",
    "CopyBrief",
    "AudienceProfile",
    "get_copywriting_engine",
    "copywriting_should_trigger",
    "copywriting_system_prompt",
]
