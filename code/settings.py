"""
AI_Agent_FSC_Developer Settings
Configurable via Cheshire Cat Admin Panel
"""

from pydantic import BaseModel, Field
from cat.mad_hatter.decorators import plugin


class FSCSettings(BaseModel):
    """
    FSC Developer Plugin Settings
    """
    
    max_fsr_per_safety_goal: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of FSRs to generate from a single Safety Goal (1-50)"
    )
    
    safety_strategy_text_length: int = Field(
        default=5,
        ge=3,
        le=15,
        description="Length of Safety Strategy text in lines (3-15 lines)"
    )

@plugin
def settings_model():
    return FSCSettings
