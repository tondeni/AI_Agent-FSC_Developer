# ====================================================================================
# tools/__init__.py
# ====================================================================================

"""
Cat-facing tool functions with @tool decorators.
All tools are automatically discovered by Cat framework.
"""

# No explicit imports needed - Cat discovers @tool decorators automatically
# But we can organize them here for documentation

__all__ = [
    # Workflow tools
    'show_fsc_workflow',
    
    # HARA tools
    'load_hara_for_fsc',
    'show_safety_goal_details',
    'show_hara_statistics',
    
    # Strategy tools
    'develop_safety_strategy',
    
    # FSR tools
    'derive_functional_safety_requirements',
    
    # Allocation tools
    'allocate_functional_requirements',
    'show_allocation_summary',
    
    # Verification tools
    'specify_safety_validation_criteria',
    'verify_functional_safety_concept'
]