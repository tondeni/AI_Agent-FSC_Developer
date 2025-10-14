# ====================================================================================
# core/__init__.py
# ====================================================================================

"""
Core domain models and constants for FSC Developer.
"""

from .models import (
    SafetyGoal,
    SafetyStrategy,
    FunctionalSafetyRequirement,
    ValidationCriterion,
    HaraData,
    FSCWorkProduct
)

from .constants import (
    ASILLevel,
    FSRType,
    AllocationType,
    SAFETY_RELEVANT_ASILS,
    FSR_TYPE_CODES,
    get_iso_reference
)

__all__ = [
    # Models
    'SafetyGoal',
    'SafetyStrategy',
    'FunctionalSafetyRequirement',
    'ValidationCriterion',
    'HaraData',
    'FSCWorkProduct',
    
    # Constants
    'ASILLevel',
    'FSRType',
    'AllocationType',
    'SAFETY_RELEVANT_ASILS',
    'FSR_TYPE_CODES',
    'get_iso_reference'
]
