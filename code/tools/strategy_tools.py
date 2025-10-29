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
    return_direct=False,
    examples=[
        "develop safety strategies for all goals",
        "develop safety strategy for SG-001",
        "create safety strategies",
        "generate strategies for goals"
    ]
)
def develop_safety_strategy(tool_input, cat):
    """STRATEGY CREATION TOOL: Develops safety strategies for safety goals.
    
    Use ONLY when user wants to CREATE/DEVELOP/GENERATE STRATEGIES FOR IDENTIFIED SAFETY GOALS
    This tool creates the 9 strategic approaches per ISO 26262.
    
    Trigger phrases: "develop strategies", "create strategies", "generate strategies"
    NOT for: viewing strategies, showing strategy details, or listing strategies
    
    Action: Generates safety strategies for each safety goal
    Prerequisites: Safety goals must be loaded via load_hara
    ISO Reference: ISO 26262-3:2018, Clause 7.4.2.3
    Input: "all goals" or specific goal ID like "SG-001"
    """
    
    log.warning(f"----------------✅ TOOL CALLED: develop_safety_strategy with input: {tool_input} ----------------")

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
        # ✅ Return string directly, not dict
        return """❌ No safety goals loaded. 
        Safety Goals are a prerequisties to develop the safety strategies. **ISO 26262-3:2018 (7.3.1) **
        You can:
         1) (Iso Clause 7.3.1)   - Load the Safety Goals from an existing HARA by typing: `load HARA for [item name]`
         2) (Iso Clause 7.4.2.3) - Develop the Safety strategy for each Safety Goal by typing: `develop safety strategy for all goals`
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
            # ✅ Return string directly
            return f"❌ Safety Goal '{sg_id}' not found."
    
    try:
        # Initialize strategy generator
        generator = StrategyGenerator(
            llm_function=cat.llm,
            strategy_text_length=strategy_text_length)
        
        # Generate strategies
        log.warning("📄 Generating safety strategies...")
        strategies = generator.generate_strategies(goals_to_process, strategy_text_length, system_name)
        
        if not strategies:
            # ✅ Return string directly
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
        cat.working_memory.last_operation = "strategy_development"
        
        # ✅ FIXED: Return MINIMAL output - let hook format the table
        output = f"""✅ Successfully developed safety strategies for {len(goals_to_process)} safety goal(s)
            **System:** {system_name}
            **Safety Goals Processed:** {len(goals_to_process)}
            """
        
        # Add validation warnings only if critical
        if validation_result.has_errors():
            output += f"\n❌ Validation: {len(validation_result.errors)} errors found\n"
            output += validation_result.format_report()
        
        log.info(f"✅ Strategies generated: {len(strategies)} safety goals")
        
        # The hook will add:
        # - Strategy table
        # - Statistics
        # - Export options
        # - Next steps
        
        return output

        # # Format output
        # formatter = StrategyFormatter()
        # output = formatter.format_strategy_summary(strategies, goals_to_process)
        
        # # Add validation summary if there are warnings
        # if validation_result.has_warnings():
        #     output += "\n\n---\n\n"
        #     output += f"⚠️ **Validation Warnings:**\n{validation_result.format_report()}\n"
        
        # log.info(f"✅ Strategies generated: {len(strategies)} safety goals")
        
        # # ✅ Return string directly - output_formatter will add next steps
        # return output
        
    except Exception as e:
        log.error(f"Error developing strategies: {e}")
        import traceback
        log.error(traceback.format_exc())
        # ✅ Return string directly
        return f"❌ Error developing strategies: {str(e)}\n\nPlease try again or check the logs."


@tool(
    return_direct=False,
    examples=[
        "show strategy for SG-001",
        "display strategy for goal 1",
        "what is the strategy for SG-002",
        "show me strategy SG-003",
        "explain strategy for SG-001"
    ]
)
def show_strategy_for_goal(tool_input, cat):
    """DETAIL TOOL: Shows complete strategy for ONE SPECIFIC safety goal by ID.
    
    Use when user requests strategy details for A SINGLE SPECIFIC SAFETY GOAL.
    Shows all 10 strategic approaches for that goal.
    
    Trigger phrases: "show strategy for SG-XXX", "strategy details for goal X"
    NOT for: creating strategies, listing all strategies, or strategy summary
    
    Displays: Complete strategy with all 10 approaches for one safety goal
    Prerequisites: Strategies must be developed first
    Input: REQUIRED - Safety goal ID like "SG-001"
    """
    
    log.warning(f"----------------✅ TOOL CALLED: show_strategy_for_goal with input: {tool_input} ----------------")
    
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
    if not strategies_data:
        # ✅ Return string directly
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
        # ✅ Return string directly
        return f"""❌ Strategy for '{sg_id}' not found.

**Available:** {available}{'...' if len(strategies_data) > 5 else ''}

**Usage:** `show strategy for SG-001`
"""
    
    # Find corresponding goal
    goal_data = next((g for g in safety_goals_data if g['id'] == sg_id), None)
    
    if not goal_data:
        # ✅ Return string directly
        return f"❌ Safety goal {sg_id} not found."
    
    # Convert to objects
    strategy = SafetyStrategy(**strategy_data)
    goal = SafetyGoal(**goal_data)
    
    # Format output
    formatter = StrategyFormatter()
    output = formatter.format_strategy_for_goal(strategy, goal)
    
    log.info(f"📋 Showed strategy for {sg_id}")
    
    # ✅ Return string directly
    return output


@tool(
    return_direct=False,
    examples=[
        "show strategy summary",
        "list strategies",
        "show all strategies overview",
        "strategy statistics"
    ]
)
def show_strategy_summary(tool_input, cat):
    """OVERVIEW TOOL: Shows summary of ALL strategies across all safety goals.
    
    Use when user wants an OVERVIEW/SUMMARY of ALL STRATEGIES.
    Shows high-level statistics and completeness status.
    
    Trigger phrases: "show strategy summary", "list all strategies", "strategy overview"
    NOT for: creating strategies, single strategy details, or specific goal strategy
    
    Displays: Total strategies, status per goal, completeness indicators
    Prerequisites: Strategies must be developed first
    Input: Not required (use empty string)
    """
    
    log.warning(f"----------------✅ TOOL CALLED: show_strategy_summary with input: {tool_input} ----------------")
    
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    system_name = cat.working_memory.get("system_name", "Unknown System")
    
    if not strategies_data:
        # ✅ Return string directly
        return "❌ No strategies developed yet. Use: `develop safety strategy for all goals`"
    
    # ✅ Return string directly with formatted summary
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
"""
    
    log.info(f"📊 Showed strategy summary: {len(strategies_data)} strategies")
    
    return summary