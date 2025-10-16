# tools/strategy_tools.py
# Safety strategy development tools

from cat.mad_hatter.decorators import tool
from cat.log import log
import sys
import os

# Add parent directory to path
plugin_folder = os.path.dirname(os.path.dirname(__file__))
sys.path.append(plugin_folder)

from generators.strategy_generator import StrategyGenerator, StrategyFormatter
from core.models import SafetyGoal, SafetyStrategy
from core.validators import StrategyValidator


@tool(
    return_direct=True,
    examples=[
        "develop safety strategy for all goals",
        "develop safety strategy for SG-001",
        "generate safety strategies",
        "create strategies for all safety goals"
    ]
)
def develop_safety_strategy(tool_input, cat):
    """
    Develop safety strategies for safety goals.    
    Input: "develop safety strategy for all goals" or "develop safety strategy for SG-XXX"
    """
    
    log.info("✅ TOOL CALLED: develop_safety_strategy")

    # ========================================================================
    # Load plugin settings
    # ========================================================================
    try:
        settings = cat.mad_hatter.get_plugin().load_settings()
        strategy_text_length = settings.get('safety_strategy_text_length', 5)
        log.info(f"📋 Settings loaded: strategy_text_length={strategy_text_length} lines")
    except Exception as e:
        log.warning(f"⚠️ Could not load settings, using defaults: {e}")
        strategy_text_length = 5  # Default fallback
    # ========================================================================

    
    # Get safety goals from working memory
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
    if not safety_goals_data:
        return """❌ No safety goals loaded.

**Required Steps per ISO 26262-3:2018:**
1. Load HARA (7.3.1): `load HARA for [item name]`
2. Develop strategy (7.4.2.3): `develop safety strategy for all goals`
"""
    
    # Convert to SafetyGoal objects
    safety_goals = [SafetyGoal(**g) for g in safety_goals_data]
    system_name = cat.working_memory.get("system_name", "the system")
    
    # Parse input to determine which goals to process
    input_str = str(tool_input).strip().lower()
    
    if "all" in input_str or input_str == "" or "safety goals" in input_str:
        goals_to_process = safety_goals
        log.info(f"🎯 Developing strategies for {len(goals_to_process)} safety goals")
    else:
        # Extract safety goal ID
        sg_id = str(tool_input).strip().upper()
        sg_id = sg_id.replace("DEVELOP SAFETY STRATEGY FOR", "").replace("SAFETY STRATEGY FOR", "").strip()
        if not sg_id.startswith('SG-'):
            sg_id = 'SG-' + sg_id.replace('SG', '').replace('-', '').strip()
        
        goals_to_process = [g for g in safety_goals if g.id == sg_id]
        
        if not goals_to_process:
            return f"❌ Safety Goal '{sg_id}' not found."
    
    try:
        # Initialize strategy generator
        generator = StrategyGenerator(
            llm_function=cat.llm,
            strategy_text_length=strategy_text_length)
        
        # Generate strategies
        log.info("🔄 Generating safety strategies...")
        strategies = generator.generate_strategies(goals_to_process, strategy_text_length, system_name)
        
        if not strategies:
            return "❌ Failed to generate strategies. Please try again."
        
        # Validate strategies
        validation_result = StrategyValidator.validate_strategies(strategies, goals_to_process)
        
        if not validation_result.passed:
            log.warning("⚠️ Strategy validation found issues")
        
        # Store in working memory
        existing_strategies = cat.working_memory.get("fsc_safety_strategies", [])
        
        # Convert to dict and merge
        new_strategies_dict = {s.safety_goal_id: s.to_dict() for s in strategies}
        existing_dict = {s['safety_goal_id']: s for s in existing_strategies}
        existing_dict.update(new_strategies_dict)
        
        cat.working_memory.fsc_safety_strategies = list(existing_dict.values())
        cat.working_memory.fsc_stage = "strategies_developed"
        
        # Format output
        formatter = StrategyFormatter()
        output = formatter.format_strategy_summary(strategies, goals_to_process)
        
        # Add validation summary
        if validation_result.has_warnings():
            output += "\n\n---\n\n"
            output += f"⚠️ **Validation Warnings:**\n{validation_result.format_report()}\n"
        
        # # Add next steps
        # workflow_section = """***ISO 26262-3:2018 - Functional Safety Concept Development Workflow***"""
    
        # completed__workflow_content ="""| Step | Phase | ISO 26262:3 clause | Status |
        # |------|-------|------------------|--------------|
        # | ✅ | Identify Safety Goals | 7.3.1 | Safety Goals extracted from HARA |
        # | ✅ | Develop Safety Strategy | 7.4.2.3 | Safety Strategies developed |"""
      
        # # # Add workflow next steps
        # pending_workflow_content = """| Step | Phase | ISO 26262:3 clause | Tool Command |
        # |------|-------|------------------|--------------|
        # | 3 | Derive Functional Safety Requirements | 7.4.2.2 | `derive FSRs for all goals` |
        # | 4 | Allocate FSRs to system architecture | 7.4.2.8 | `allocate all FSRs` |
        # | 5 | Specify Validation Criteria | 7.4.3 | `specify validation criteria` |
        # | 6 | Verify FSC | 7.4.4 | `verify FSC` |
        # | 7 | Generate FSC Document | 7.5 | `generate FSC document` |"""
       
        # log.info(f"✅ Strategies generated: {len(strategies)} safety goals")
        # output += workflow_section + "\n " + completed__workflow_content + "\n **Next Steps** \n" + pending_workflow_content
        return output
        
    except Exception as e:
        log.error(f"Error developing strategies: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error developing strategies: {str(e)}\n\nPlease try again or check the logs."


@tool(return_direct=True)
def show_strategy_for_goal(tool_input, cat):
    """
    Show detailed strategy for a specific safety goal.
    
    Input: Safety goal ID (e.g., "SG-001")
    Example: "show strategy for SG-001"
    """
    
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
    if not strategies_data:
        return "❌ No strategies developed yet. Use: `develop safety strategy for all goals`"
    
    # Parse input
    sg_id = str(tool_input).strip().upper()
    sg_id = sg_id.replace("SHOW STRATEGY FOR", "").replace("STRATEGY FOR", "").strip()
    if not sg_id.startswith('SG-'):
        sg_id = 'SG-' + sg_id.replace('SG', '').replace('-', '').strip()
    
    # Find strategy
    strategy_data = next((s for s in strategies_data if s['safety_goal_id'] == sg_id), None)
    
    if not strategy_data:
        available = ', '.join([s['safety_goal_id'] for s in strategies_data[:5]])
        return f"""❌ Strategy for '{sg_id}' not found.

**Available:** {available}{'...' if len(strategies_data) > 5 else ''}

**Usage:** `show strategy for SG-001`
"""
    
    # Find corresponding goal
    goal_data = next((g for g in safety_goals_data if g['id'] == sg_id), None)
    
    if not goal_data:
        return f"❌ Safety goal {sg_id} not found."
    
    # Convert to objects
    strategy = SafetyStrategy(**strategy_data)
    goal = SafetyGoal(**goal_data)
    
    # Format output
    formatter = StrategyFormatter()
    output = formatter.format_strategy_for_goal(strategy, goal)
    
    return output


@tool(return_direct=True)
def show_strategy_summary(tool_input, cat):
    """
    Show summary of all developed strategies.
    
    Input: "show strategy summary" or "list strategies"
    """
    
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    system_name = cat.working_memory.get("system_name", "Unknown System")
    
    if not strategies_data:
        return "❌ No strategies developed yet. Use: `develop safety strategy for all goals`"
    
    summary = f"""# 📋 Safety Strategy Summary

**System:** {system_name}
**Safety Goals with Strategies:** {len(strategies_data)}

---

## Overview

"""
    
    for strategy_data in strategies_data:
        sg_id = strategy_data['safety_goal_id']
        goal_data = next((g for g in safety_goals_data if g['id'] == sg_id), None)
        
        if not goal_data:
            continue
        
        summary += f"### {sg_id}\n"
        summary += f"**Goal:** {goal_data['description'][:80]}...\n" if len(goal_data['description']) > 80 else f"**Goal:** {goal_data['description']}\n"
        summary += f"**ASIL:** {goal_data['asil']}\n"
        
        # Check completeness
        strategies = strategy_data.get('strategies', {})
        complete = len(strategies) >= 10  # All 9 strategies + extras
        
        summary += f"**Status:** {'✅ Complete' if complete else '⚠️ Incomplete'}\n"
        summary += f"**Strategies Defined:** {len(strategies)}/10 required\n\n"
    
    summary += """---

**View Detailed Strategy:** `show strategy for SG-XXX`

**Next Step:** `derive FSRs for all goals`
"""
    
    return summary