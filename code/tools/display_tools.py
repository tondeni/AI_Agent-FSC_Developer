from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import sys
import os


@tool(
    return_direct=True,
    examples=[
        "show FSR summary",
        "list all FSRs",
        "display functional safety requirements"
    ]
)
def show_fsr_summary(tool_input, cat):
    """
    Display summary of all derived Functional Safety Requirements.
    """
    
    log.info("🔧 TOOL CALLED: show_fsr_summary")
    
    fsrs = cat.working_memory.get('fsc_functional_requirements', [])
    system_name = cat.working_memory.get('system_name', 'System')
    
    if not fsrs:
        return "No FSRs found. Please derive FSRs first with: derive FSRs for all goals"
    
    # ✅ SIMPLE PLAIN TEXT OUTPUT
    output = f"Functional Safety Requirements Summary for {system_name}\n\n"
    output += f"Total FSRs: {len(fsrs)}\n\n"
    
    # List all FSRs
    for fsr in fsrs:
        output += f"{fsr['id']} ({fsr['type']}, ASIL {fsr['asil']})\n"
        output += f"  Description: {fsr['description']}\n"
        output += f"  Safety Goal: {fsr['safety_goal_id']}\n"
        output += f"  Allocated to: {fsr.get('allocated_to', 'Not allocated')}\n"
        output += "\n"
    
    return output


@tool(
    return_direct=True,
    examples=[
        "show workflow status",
        "what's my progress",
        "show FSC status"
    ]
)
def show_fsc_workflow_status(tool_input, cat):
    """
    Display current FSC development workflow status.
    """
    
    log.info("🔧 TOOL CALLED: show_fsc_workflow_status")
    
    # Get workflow state
    stage = cat.working_memory.get('fsc_stage', 'Not started')
    system_name = cat.working_memory.get('system_name', 'Not set')
    goals = cat.working_memory.get('fsc_safety_goals', [])
    strategies = cat.working_memory.get('fsc_safety_strategies', [])
    fsrs = cat.working_memory.get('fsc_functional_requirements', [])
    
    # ✅ SIMPLE PLAIN TEXT OUTPUT
    output = f"FSC Development Workflow Status\n\n"
    output += f"System: {system_name}\n"
    output += f"Current Stage: {stage}\n\n"
    
    output += "Progress:\n"
    output += f"  Step 1 - Load HARA: {'✓ Complete' if goals else '✗ Not started'} ({len(goals)} goals)\n"
    output += f"  Step 2 - Develop Strategies: {'✓ Complete' if strategies else '✗ Not started'} ({len(strategies)} strategies)\n"
    output += f"  Step 3 - Derive FSRs: {'✓ Complete' if fsrs else '✗ Not started'} ({len(fsrs)} FSRs)\n"
    output += f"  Step 4 - Allocate FSRs: {'✓ Complete' if any(f.get('allocated_to') != 'TBD' for f in fsrs) else '✗ Not started'}\n"
    output += f"  Step 5 - Validation Criteria: {cat.working_memory.get('fsc_stage') == 'validation_criteria_specified' and '✓ Complete' or '✗ Not started'}\n"
    output += f"  Step 6 - Verify FSC: {cat.working_memory.get('fsc_stage') == 'fsc_verified' and '✓ Complete' or '✗ Not started'}\n"
    
    return output