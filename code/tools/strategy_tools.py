# File: code/tools/strategy_tools.py

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import sys
import os

# Add plugin folder to path (your existing pattern)
plugin_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(plugin_folder)

# Your existing imports - these work!
from generators.fsr_generator import FSRGenerator
from core.models import SafetyGoal, SafetyStrategy, FunctionalSafetyRequirement
from core.validators import FSRValidator



@tool(
    return_direct=True,
    examples=[
        "develop safety strategies for all goals",
        "develop safety strategy for SG-001",
        "create strategies"
    ]
)
def develop_safety_strategy(tool_input, cat):
    """
    Develop comprehensive safety strategies for safety goals.
    
    Creates 9 strategy types per ISO 26262-3:2018, Clause 7.4.2.3.
    
    Input: "all goals" or specific goal ID (e.g., "SG-001")
    """
    
    log.info("🔧 TOOL CALLED: develop_safety_strategy")
    
    # Get data
    goals = cat.working_memory.get('fsc_safety_goals', [])
    system_name = cat.working_memory.get('system_name', 'System')
    
    if not goals:
        return "Error: No safety goals loaded. Please load HARA first with: load HARA for [system name]"
    
    # Parse input to determine which goals to process
    user_input = tool_input.lower().strip()
    
    if 'all' in user_input:
        goals_to_process = goals
    else:
        # Try to find specific goal ID
        goal_id = user_input.upper().replace('SG-', 'SG-')
        goals_to_process = [g for g in goals if g.get('id') == goal_id]
        
        if not goals_to_process:
            return f"Error: Could not find safety goal '{user_input}'. Available goals: " + \
                   ", ".join([g.get('id') for g in goals])
    
    try:
        # Import generator
        from generators.strategy_generator import StrategyGenerator
        from core.validators import StrategyValidator
        
        # Get plugin settings
        settings = cat.mad_hatter.get_plugin().load_settings()
        strategy_text_length = settings.get('strategy_text_length', 5)
        
        log.info(f"Using strategy_text_length: {strategy_text_length} lines")
        
        # Convert dictionary goals to SafetyGoal objects
        safety_goal_objects = []
        for goal_dict in goals_to_process:
            try:
                # Create SafetyGoal object from dictionary
                goal_obj = SafetyGoal.from_dict(goal_dict)
                safety_goal_objects.append(goal_obj)
            except Exception as e:
                log.warning(f"Failed to convert goal {goal_dict.get('id', 'unknown')}: {e}")
                continue
        
        if not safety_goal_objects:
            return "Error: Could not convert safety goals to proper format. Please reload HARA data."
        
        # Generate strategies
        generator = StrategyGenerator(
            llm_function=cat.llm,
            strategy_text_length=strategy_text_length
        )
        strategies = generator.generate_strategies(safety_goal_objects, system_name)
        
        if not strategies:
            return "Error: Failed to generate strategies. Please try again."
        
        # Validate
        validation_result = StrategyValidator.validate_strategies(strategies, safety_goal_objects)
        
        # Store in working memory
        existing_strategies = cat.working_memory.get('fsc_safety_strategies', [])
        new_strategies_dict = {s.safety_goal_id: s.to_dict() for s in strategies}
        existing_dict = {s['safety_goal_id']: s for s in existing_strategies}
        existing_dict.update(new_strategies_dict)
        
        cat.working_memory['fsc_safety_strategies'] = list(existing_dict.values())
        cat.working_memory['fsc_stage'] = 'strategies_developed'
        cat.working_memory['needs_formatting'] = True
        cat.working_memory['last_operation'] = 'strategy_development'
        
        # ✅ SIMPLE PLAIN TEXT OUTPUT
        output = f"Successfully developed safety strategies for {system_name}.\n\n"
        output += f"Generated {len(strategies)} strategies for {len(safety_goal_objects)} safety goal(s).\n"
        output += "Each safety goal has 9 strategy types as required by ISO 26262-3:2018, Clause 7.4.2.3.\n\n"
        
        # List strategies in simple format
        for goal_obj in safety_goal_objects:
            goal_id = goal_obj.id
            goal_desc = goal_obj.description
            goal_asil = goal_obj.asil
            
            output += f"Safety Goal {goal_id} (ASIL {goal_asil}): {goal_desc}\n"
            
            # Get strategies for this goal
            goal_strategies = [s for s in strategies if s.safety_goal_id == goal_id]
            
            if goal_strategies:
                strategy = goal_strategies[0]
                # List each strategy type
                for strategy_type, strategy_content in strategy.strategies.items():
                    strategy_name = strategy_type.replace('_', ' ').title()
                    # Show first line of strategy as preview
                    preview = strategy_content.split('\n')[0][:80] + "..." if len(strategy_content) > 80 else strategy_content.split('\n')[0]
                    output += f"  - {strategy_name}: {preview}\n"
            
            output += "\n"
        
        # Add validation warnings if critical
        if validation_result.has_errors():
            output += f"Warning: Validation found {len(validation_result.errors)} errors.\n"
            for error in validation_result.errors[:3]:
                output += f"  - {error}\n"
        
        log.info(f"✅ Generated {len(strategies)} strategies")
        
        return output
        
    except Exception as e:
        log.error(f"Error developing strategies: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"Error developing strategies: {str(e)}"