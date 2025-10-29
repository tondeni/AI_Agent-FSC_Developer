from pydantic import BaseModel, Field
from cat.mad_hatter.decorators import plugin

class FSCDeveloperSettings(BaseModel):
    """FSC Developer Plugin Configuration"""
    
    max_fsrs_per_goal: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum FSRs to generate per safety goal"
    )
    
    llm_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="LLM temperature for generation (lower = more deterministic)"
    )
    
    enable_auto_validation: bool = Field(
        default=True,
        description="Automatically validate artifacts after generation"
    )
    
    default_output_format: str = Field(
        default="standard",
        description="Default output format (standard/minimal/detailed)"
    )
    
    strategy_text_length: int = Field(
        default=5,
        ge=3,
        le=15,
        description="Maximum number of lines for each safety strategy description"
    )

@plugin
def settings_model():
    return FSCDeveloperSettings