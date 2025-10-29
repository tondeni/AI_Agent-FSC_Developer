# tools/fsr_tools.py
# FSR derivation tools - FIXED VERSION

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

def dict_to_safety_goal(goal_dict: dict) -> SafetyGoal:
    """Manually convert dict to SafetyGoal"""
    return SafetyGoal(
        id=goal_dict.get('id'),
        description=goal_dict.get('description'),
        asil=goal_dict.get('asil'),
        safe_state=goal_dict.get('safe_state'),
        ftti=goal_dict.get('ftti')
    )


def dict_to_safety_strategy(strategy_dict: dict) -> SafetyStrategy:
    """Manually convert dict to SafetyStrategy"""
    return SafetyStrategy(
        safety_goal_id=strategy_dict.get('safety_goal_id'),
        strategies=strategy_dict.get('strategies', {})
    )

def get_fsr_type(fsr) -> str:
    """
    Get FSR type from multiple possible attribute names.
    FSR objects might use 'type', 'requirement_type', or 'fsr_type'.
    """
    # Try different attribute names
    for attr_name in ['type', 'requirement_type', 'fsr_type', 'category']:
        if hasattr(fsr, attr_name):
            value = getattr(fsr, attr_name)
            if value and value != 'Unknown':
                return value
    
    # Fallback: extract from FSR ID (e.g., FSR-SG-001-DET-1 → DET → Detection)
    try:
        fsr_id = fsr.id
        if '-' in fsr_id:
            parts = fsr_id.split('-')
            if len(parts) >= 4:
                type_code = parts[3]  # DET, CTL, WRN, etc.
                type_map = {
                    'DET': 'Detection',
                    'CTL': 'Control',
                    'WRN': 'Warning',
                    'AVD': 'Avoidance',
                    'SFS': 'Safe State',
                    'TOL': 'Tolerance',
                    'TIM': 'Timing',
                    'ARB': 'Arbitration'
                }
                return type_map.get(type_code, type_code)
    except:
        pass
    
    return 'Detection'  # Default fallback

def format_fsr_table(fsrs, goal_objects, system_name):
    """
    Format FSRs as a clean markdown table.
    This prevents the output formatter hook from calling LLM again.
    """
    
    # Group FSRs by safety goal
    fsrs_by_goal = {}
    for fsr in fsrs:
        goal_id = fsr.safety_goal_id
        if goal_id not in fsrs_by_goal:
            fsrs_by_goal[goal_id] = []
        fsrs_by_goal[goal_id].append(fsr)
    
    output = f"✅ **Successfully derived Functional Safety Requirements for {system_name}**\n\n"
    output += f"*ISO 26262-3:2018, Clause 7.4.2 - Functional Safety Requirements*\n\n"
    output += f"**Total:** {len(fsrs)} FSRs from {len(goal_objects)} safety goal(s)\n\n"
    
    # Create comprehensive table
    output += "## 📋 Functional Safety Requirements\n\n"
    output += "| FSR-ID | Type | ASIL | Safety Goal | Description | Allocation |\n"
    output += "|--------|------|------|-------------|-------------|------------|\n"
    
    for goal_id in sorted(fsrs_by_goal.keys()):
        goal_fsrs = fsrs_by_goal[goal_id]
        
        for fsr in goal_fsrs:
            # Get FSR details
            fsr_id = fsr.id
            
            # ✅ FIX 1: Get type correctly (try multiple attributes)
            fsr_type = get_fsr_type(fsr)
            
            fsr_asil = fsr.asil
            fsr_goal = fsr.safety_goal_id
            
            # ✅ FIX 2: Keep full description (no truncation)
            desc = fsr.description
            # Just clean up for table display (remove pipes and newlines)
            desc = desc.replace('\n', ' ').replace('|', '\\|').strip()
            
            # Allocation
            allocation = getattr(fsr, 'allocated_to', 'TBD')
            if not allocation or allocation == 'None':
                allocation = 'TBD'
            
            # Add row
            output += f"| {fsr_id} | {fsr_type} | {fsr_asil} | {fsr_goal} | {desc} | {allocation} |\n"
    
    output += "\n"
    
    # Add ASIL distribution
    asil_counts = {}
    for fsr in fsrs:
        asil = fsr.asil
        asil_counts[asil] = asil_counts.get(asil, 0) + 1
    
    output += "### 📊 ASIL Distribution\n\n"
    for asil in ['D', 'C', 'B', 'A', 'QM']:
        if asil in asil_counts:
            count = asil_counts[asil]
            percentage = (count / len(fsrs) * 100) if fsrs else 0
            output += f"- **ASIL {asil}**: {count} FSRs ({percentage:.1f}%)\n"
    
    # Add type distribution
    # type_counts = {}
    # for fsr in fsrs:
    #     fsr_type = getattr(fsr, 'requirement_type', 'Unknown')
    #     type_counts[fsr_type] = type_counts.get(fsr_type, 0) + 1
    
    # output += "\n### 📂 Type Distribution\n\n"
    # for fsr_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    #     percentage = (count / len(fsrs) * 100) if fsrs else 0
    #     output += f"- **{fsr_type}**: {count} FSRs ({percentage:.1f}%)\n"
    
    # Add summary by goal
    # output += "\n### 🎯 FSRs by Safety Goal\n\n"
    # for goal_id in sorted(fsrs_by_goal.keys()):
    #     goal = next((g for g in goal_objects if g.id == goal_id), None)
    #     goal_fsrs = fsrs_by_goal[goal_id]
        
        # if goal:
        #     output += f"**{goal_id}** (ASIL {goal.asil}): {len(goal_fsrs)} FSRs\n"
        #     output += f"  ↳ {goal.description}\n"
        # else:
        #     output += f"**{goal_id}**: {len(goal_fsrs)} FSRs\n"
    
    output += "\n---\n\n"
    output += "**Next Steps:**\n"
    output += "- 📊 Export to Excel: `export FSRs to excel`\n"
    output += "- 📄 Generate Word doc: `create fsc word document`\n"
    output += "- 🔍 Review specific FSR: `show FSR [FSR-ID]`\n"
    
    return output

@tool(
    return_direct=True,
    examples=[
        "derive FSRs for all goals",
        "derive functional safety requirements",
        "create FSRs"
    ]
)
def derive_functional_safety_requirements(tool_input, cat):
    """
    Derive Functional Safety Requirements (FSRs) from safety strategies.
    
    Creates FSRs per ISO 26262-3:2018, Clause 7.4.2.
    Returns pre-formatted output to avoid slow LLM reformatting.
    
    Input: "all goals" or specific goal ID
    """
    
    log.info("🔧 TOOL CALLED: derive_functional_safety_requirements")
    
    # Get data from working memory
    goals = cat.working_memory.get('fsc_safety_goals', [])
    strategies = cat.working_memory.get('fsc_safety_strategies', [])
    system_name = cat.working_memory.get('system_name', 'System')
    
    if not goals:
        return "❌ Error: No safety goals loaded. Please load HARA first."
    
    if not strategies:
        return "❌ Error: No safety strategies found. Please develop strategies first."
    
    log.info(f"📊 Found {len(goals)} goals and {len(strategies)} strategies")
    
    try:
        # Get plugin settings
        try:
            settings = cat.mad_hatter.get_plugin().load_settings()
            max_fsr_per_safety_goal = settings.get('max_fsrs_per_goal', 10)
            log.info(f"Max FSRs per goal: {max_fsr_per_safety_goal}")
        except Exception as e:
            log.warning(f"⚠️ Failed to load settings: {e}")
            max_fsr_per_safety_goal = 10
        
        log.info(f"🔄 Converting goals and strategies...")
        
        # Convert goals to SafetyGoal objects
        goal_objects = []
        for i, goal_dict in enumerate(goals):
            try:
                if isinstance(goal_dict, SafetyGoal):
                    goal_objects.append(goal_dict)
                else:
                    goal_obj = dict_to_safety_goal(goal_dict)
                    goal_objects.append(goal_obj)
            except Exception as e:
                log.error(f"❌ Failed to convert goal {i+1}: {e}")
                continue
        
        if not goal_objects:
            return "❌ Error: Could not convert any safety goals."
        
        # Convert strategies to SafetyStrategy objects
        strategy_objects = []
        for i, strategy_dict in enumerate(strategies):
            try:
                if isinstance(strategy_dict, SafetyStrategy):
                    strategy_objects.append(strategy_dict)
                else:
                    strategy_obj = dict_to_safety_strategy(strategy_dict)
                    strategy_objects.append(strategy_obj)
            except Exception as e:
                log.error(f"❌ Failed to convert strategy {i+1}: {e}")
                continue
        
        if not strategy_objects:
            return "❌ Error: Could not convert any strategies."
        
        log.info(f"✅ Converted {len(goal_objects)} goals and {len(strategy_objects)} strategies")
        
        # Initialize generator
        log.info(f"🚀 Initializing FSRGenerator...")
        generator = FSRGenerator(
            llm_function=cat.llm,
            max_fsr_per_safety_goal=max_fsr_per_safety_goal
        )
        
        # Generate FSRs
        log.info(f"🚀 Generating FSRs...")
        fsrs = generator.generate_fsrs(
            safety_goals=goal_objects,
            strategies=strategy_objects,
            max_fsr_per_safety_goal=max_fsr_per_safety_goal,
            system_name=system_name
        )
        
        if not fsrs:
            return "❌ Error: Failed to generate FSRs."
        
        log.info(f"✅ Generated {len(fsrs)} FSRs")
        
        # Validate (optional)
        # try:
        #     validation_result = FSRValidator.validate_fsrs(fsrs, goal_objects)
        #     log.info(f"✅ Validation complete")
        # except Exception as e:
        #     log.warning(f"⚠️ Validation skipped: {e}")
        #     validation_result = None
        
        # Store in working memory
        log.info(f"💾 Storing FSRs...")
        fsrs_as_dicts = []
        for fsr in fsrs:
            if hasattr(fsr, 'to_dict'):
                fsrs_as_dicts.append(fsr.to_dict())
            else:
                # Manual conversion
                fsrs_as_dicts.append({
                    'id': fsr.id,
                    'safety_goal_id': fsr.safety_goal_id,
                    'description': fsr.description,
                    'type': getattr(fsr, 'requirement_type', 'Detection'),
                    'asil': fsr.asil,
                    'safe_state': getattr(fsr, 'safe_state', None),
                    'ftti': getattr(fsr, 'ftti', None),
                    'verification_method': getattr(fsr, 'verification_method', None),
                    'allocated_to': getattr(fsr, 'allocated_to', None)
                })
        
        cat.working_memory['fsc_functional_requirements'] = fsrs_as_dicts
        cat.working_memory['fsc_stage'] = 'fsrs_derived'
        cat.working_memory['needs_formatting'] = False
        cat.working_memory['last_operation'] = 'fsr_derivation'
        
        log.info(f"✅ Stored {len(fsrs_as_dicts)} FSRs")
        
        # ✅ CRITICAL: Return pre-formatted table to avoid LLM reformatting
        log.info(f"📝 Formatting output...")
        formatted_output = format_fsr_table(fsrs, goal_objects, system_name)
        
        log.info(f"✅ FSR derivation complete!")
        
        return formatted_output
        
    except Exception as e:
        log.error(f"❌ Error deriving FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error deriving FSRs: {str(e)}"


# @tool(
#     return_direct=False,
#     examples=[
#         "show FSR summary",
#         "list all FSRs",
#         "show functional safety requirements",
#         "show all FSRs",
#         "display FSR overview",
#         "what FSRs do we have",
#         "FSR summary",
#         "show me the FSRs",
#         "list functional safety requirements",
#         "display all FSRs",
#         "show FSR statistics",
#         "FSR overview"
#     ]
# )
# def show_fsr_summary(tool_input, cat):
#     """
#     Use this tool to show a summary of all derived Functional Safety Requirements (FSRs).
    
#     This tool MUST be used when the user asks to:
#     - show FSR summary
#     - list all FSRs
#     - display FSRs
#     - view FSR overview
#     - see FSR statistics
#     - show functional safety requirements
#     - get FSR information
    
#     The tool displays:
#     - Total number of FSRs
#     - Distribution by ASIL level (D, C, B, A, QM)
#     - Distribution by FSR type (Detection, Control, Warning, etc.)
#     - Distribution by Safety Goal
#     - Allocation status
    
#     Prerequisites: FSRs must be derived first using derive_functional_safety_requirements tool.
    
#     Input: Not required (can be empty or "all" or "summary")
#     """
    
#     log.warning(f"----------------✅ TOOL CALLED: show_fsr_summary with input: {tool_input}")
    
#     fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
#     system_name = cat.working_memory.get("system_name", "Unknown System")
    
#     if not fsrs_data:
#         # ✅ FIXED: Return string directly
#         return "No FSRs derived yet. Use: derive FSRs for all goals"
    
#     # Calculate statistics
#     total = len(fsrs_data)
#     by_type = {}
#     by_asil = {}
#     by_goal = {}
#     allocated_count = 0
    
#     for fsr in fsrs_data:
#         # Count by type
#         fsr_type = fsr.get('type', 'Unknown')
#         by_type[fsr_type] = by_type.get(fsr_type, 0) + 1
        
#         # Count by ASIL
#         asil = fsr.get('asil', 'QM')
#         by_asil[asil] = by_asil.get(asil, 0) + 1
        
#         # Count by safety goal
#         sg_id = fsr.get('safety_goal_id', 'Unknown')
#         by_goal[sg_id] = by_goal.get(sg_id, 0) + 1
        
#         # Count allocated
#         if fsr.get('allocated_to') and fsr.get('allocated_to') != 'TBD':
#             allocated_count += 1
    
#     # ✅ FIXED: Return string directly
#     output = f"""📊 **FSR Summary for {system_name}**

# **Total FSRs:** {total}

# **Distribution by ASIL:**
# """
    
#     for asil in ['D', 'C', 'B', 'A', 'QM']:
#         if asil in by_asil:
#             output += f"- ASIL {asil}: {by_asil[asil]} FSRs\n"
    
#     output += "\n**Distribution by Type:**\n"
#     for fsr_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
#         output += f"- {fsr_type}: {count} FSRs\n"
    
#     output += f"\n**Distribution by Safety Goal:**\n"
#     for sg_id, count in sorted(by_goal.items()):
#         output += f"- {sg_id}: {count} FSRs\n"
    
#     output += f"\n**Allocation Status:** {allocated_count}/{total} FSRs allocated"
    
#     output += "\n\n**Commands:**"
#     output += "\n- View specific FSR: `show FSR FSR-SG-001-DET-1`"
#     output += "\n- Allocate FSRs: `allocate all FSRs`"
    
#     log.info(f"📊 Showed FSR summary: {total} FSRs")
    
#     return output


# @tool(
#     return_direct=False,
#     examples=[
#         "show FSR FSR-SG-001-DET-1",
#         "show details for FSR-001",
#         "explain FSR-SG-002-CTL-1",
#         "what is FSR-SG-001-DET-1",
#         "show me FSR-001",
#         "display FSR FSR-SG-003-WRN-1",
#         "details of FSR-SG-001-CTL-2",
#         "explain FSR 001",
#         "show FSR details for FSR-SG-002-DET-1",
#         "get information about FSR-001",
#         "tell me about FSR-SG-001-DET-1"
#     ]
# )
# def show_fsr_details(tool_input, cat):
#     """
#     Use this tool to show detailed information for a specific Functional Safety Requirement (FSR).
    
#     This tool MUST be used when the user asks to:
#     - show FSR details
#     - explain a specific FSR
#     - display FSR information
#     - show FSR [ID]
#     - what is FSR-[ID]
#     - get details about FSR-[ID]
#     - tell me about FSR-[ID]
    
#     The tool displays complete FSR information including:
#     - FSR ID and type
#     - Full description
#     - Linked Safety Goal
#     - ASIL level
#     - Allocation target (HW/SW component)
#     - Verification criteria
#     - Timing requirements (FTTI)
#     - Safe state definition
#     - Operating modes
    
#     Prerequisites: FSRs must be derived first.
    
#     Input: FSR ID in format "FSR-SG-XXX-YYY-Z" (e.g., "FSR-SG-001-DET-1")
#     The tool accepts various formats:
#     - "FSR-SG-001-DET-1"
#     - "FSR-001-DET-1" 
#     - "001-DET-1"
#     - "SG-001-DET-1"
#     """
    
#     log.warning(f"----------------✅ TOOL CALLED: show_fsr_details with input: {tool_input}")
    
#     fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
#     if not fsrs_data:
#         # ✅ FIXED: Return string directly
#         return "No FSRs available. Please derive FSRs first using: derive FSRs for all goals"
    
#     # Parse FSR ID from input
#     fsr_id = str(tool_input).strip().upper()
#     fsr_id = fsr_id.replace("SHOW FSR", "").replace("SHOW", "").replace("FSR", "").strip()
    
#     if not fsr_id.startswith('FSR-'):
#         fsr_id = 'FSR-' + fsr_id
    
#     # Find the FSR
#     fsr_data = next((f for f in fsrs_data if f['id'] == fsr_id), None)
    
#     if not fsr_data:
#         available_ids = [f['id'] for f in fsrs_data[:5]]
#         # ✅ FIXED: Return string directly
#         return f"FSR '{fsr_id}' not found.\n\nAvailable FSRs: {', '.join(available_ids)}{'...' if len(fsrs_data) > 5 else ''}"
    
#     # ✅ FIXED: Return string directly with formatted details
#     output = f"""📋 **{fsr_id}** - {fsr_data.get('type', 'Unknown Type')}

# **Description:**
# {fsr_data.get('description', 'Not specified')}

# **Safety Goal:** {fsr_data.get('safety_goal_id', 'Unknown')}
# *{fsr_data.get('safety_goal', 'Not specified')}*

# **ASIL Level:** {fsr_data.get('asil', 'QM')}

# **Allocated To:** {fsr_data.get('allocated_to', 'TBD')}

# **Verification Criteria:**
# {fsr_data.get('verification_criteria', 'Not specified')}

# **Timing Requirements:** {fsr_data.get('timing', 'Not specified')}

# **Safe State:** {fsr_data.get('safe_state', 'Not specified')}

# **Operating Modes:** {fsr_data.get('operating_modes', 'All modes')}
# """
    
#     log.info(f"📋 Showed details for {fsr_id}")
    
#     return output


# @tool(
#     return_direct=False,
#     examples=[
#         "list FSRs for SG-001",
#         "show FSRs for safety goal 1",
#         "what FSRs are linked to SG-002"
#     ]
# )
# def list_fsrs_for_goal(tool_input, cat):
#     """
#     List all FSRs for a specific safety goal.
    
#     Input: Safety goal ID (e.g., "SG-001")
#     """
    
#     log.warning(f"----------------✅ TOOL CALLED: list_fsrs_for_goal with input: {tool_input}")
    
#     fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
#     goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
#     if not fsrs_data:
#         # ✅ FIXED: Return string directly
#         return "No FSRs available. Please derive FSRs first."
    
#     # Parse safety goal ID
#     sg_id = str(tool_input).strip().upper()
#     sg_id = sg_id.replace("FOR", "").replace("GOAL", "").replace("SAFETY", "").strip()
    
#     if not sg_id.startswith('SG-'):
#         sg_id = 'SG-' + sg_id.replace('SG', '').replace('-', '').strip()
    
#     # Find matching FSRs
#     matching_fsrs = [f for f in fsrs_data if f.get('safety_goal_id') == sg_id]
    
#     if not matching_fsrs:
#         # ✅ FIXED: Return string directly
#         return f"No FSRs found for safety goal {sg_id}."
    
#     # Find the safety goal info
#     goal_info = next((g for g in goals_data if g.get('id') == sg_id), None)
    
#     # ✅ FIXED: Return string directly
#     output = f"""📋 **FSRs for {sg_id}**

# """
    
#     if goal_info:
#         output += f"**Safety Goal:** {goal_info.get('description', 'Not specified')}\n"
#         output += f"**ASIL:** {goal_info.get('asil', 'Unknown')}\n\n"
    
#     output += f"**Total FSRs:** {len(matching_fsrs)}\n\n"
    
#     # Group by type
#     by_type = {}
#     for fsr in matching_fsrs:
#         fsr_type = fsr.get('type', 'Unknown')
#         if fsr_type not in by_type:
#             by_type[fsr_type] = []
#         by_type[fsr_type].append(fsr)
    
#     for fsr_type, fsrs in sorted(by_type.items()):
#         output += f"**{fsr_type}:**\n"
#         for fsr in fsrs:
#             output += f"- {fsr['id']}: {fsr.get('description', 'Not specified')[:80]}...\n"
#         output += "\n"
    
#     log.info(f"📋 Listed {len(matching_fsrs)} FSRs for {sg_id}")
    
#     return output


# @tool(
#     return_direct=False,
#     examples=[
#         "generate structured FSC content",
#         "create complete FSC with templates",
#         "build FSC using templates"
#     ]
# )
# def generate_structured_fsc_content(tool_input, cat):
#     """
#     Generate complete, structured FSC content using template-based approach.
    
#     Output is stored as pure dictionary in working memory - no classes needed.
#     Contract-based: Output Formatter can read this without importing anything.
    
#     Prerequisites:
#     - Safety goals must be loaded (from HARA)
    
#     Input: Not needed
#     """
#     # IMPORTANT ***
#     # Input: system architecture description when available 
#     log.warning(f"----------------✅ TOOL CALLED: generate_structured_fsc_content with input: {tool_input}")
    
#     # Import only local helpers
#     import sys
#     import os
#     code_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     sys.path.insert(0, code_folder)
    
#     from models.fsc_templates import FSCContentTemplate
#     from models.fsc_content_models import (
#         create_fsr_dict,
#         create_safety_mechanism_dict,
#         create_fsc_content_dict,
#         validate_fsc_content,
#         get_fsc_statistics,
#         format_fsc_summary
#     )
#     import json
#     import re
    
#     # Get prerequisites
#     goals_data = cat.working_memory.get("fsc_safety_goals", [])
#     system_name = cat.working_memory.get("system_name", "Unknown System")
#     architecture_desc = tool_input.strip() if tool_input.strip() else "To be defined"
    
#     if not goals_data:
#         return """❌ No safety goals loaded. 

# **Required:**
# 1. Load HARA: `load HARA for [system]`

# Then retry: `generate structured FSC content`"""
    
#     # Initialize template
#     template = FSCContentTemplate()
    
#     # Prepare context
#     goals_list = "\n".join([
#         f"- {g.get('id', 'SG-?')}: {g.get('goal', 'Unknown')} (ASIL {g.get('asil', '?')})"
#         for g in goals_data
#     ])
    
#     # Collect generated content
#     introduction = ""
#     safety_goal_summary = ""
#     all_fsrs = []
#     all_sms = []
#     architectural_allocation = ""
#     verification_strategy = ""
    
#     log.info(f"📝 Generating structured FSC for {system_name}")
    
#     # 1. Introduction
#     log.info("Generating: introduction")
#     intro_context = {
#         'item_name': system_name,
#         'item_context': f"System with {len(goals_data)} safety goals requiring FSC per ISO 26262-3:2018"
#     }
#     intro_prompt = template.get_prompt('introduction', intro_context)
#     introduction = cat.llm(intro_prompt).strip()
    
#     # 2. Safety Goal Summary
#     log.info("Generating: safety_goal_summary")
#     sg_context = {'safety_goals_list': goals_list}
#     sg_prompt = template.get_prompt('safety_goal_summary', sg_context)
#     safety_goal_summary = cat.llm(sg_prompt).strip()
    
#     # 3. FSRs (per goal)
#     log.info("Generating: FSRs")
    
#     # Get strategies - handle both dict and list formats
#     strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    
#     for goal in goals_data:
#         goal_id = goal.get('id', 'SG-?')
        
#         # Handle both dict (keyed by goal_id) and list formats
#         if isinstance(strategies_data, dict):
#             goal_strategies = strategies_data.get(goal_id, {})
#         elif isinstance(strategies_data, list):
#             # Filter strategies for this goal from list
#             goal_strategies = [s for s in strategies_data if s.get('safety_goal_id') == goal_id]
#         else:
#             goal_strategies = {}
        
#         strategies_text = json.dumps(goal_strategies, indent=2) if goal_strategies else "Standard strategies per ISO 26262-3"
        
#         fsr_context = {
#             'safety_goal': goal.get('goal', ''),
#             'asil': goal.get('asil', 'QM'),
#             'goal_id': goal_id.replace('SG-', ''),
#             'strategies': strategies_text
#         }
        
#         fsr_prompt = template.get_prompt('functional_safety_requirements', fsr_context)
#         fsr_response = cat.llm(fsr_prompt)
        
#         # Parse JSON
#         try:
#             fsr_response_clean = re.sub(r'```json\s*|\s*```', '', fsr_response)
#             fsr_json = json.loads(fsr_response_clean)
            
#             for fsr_data in fsr_json:
#                 # Use helper function to create FSR dict
#                 fsr_dict = create_fsr_dict(
#                     id=fsr_data['id'],
#                     description=fsr_data['description'],
#                     type=fsr_data['type'],
#                     asil=fsr_data['asil'],
#                     safety_goal_id=goal_id,
#                     safe_state=fsr_data['safe_state'],
#                     ftti=fsr_data['ftti'],
#                     validation_criteria=fsr_data['validation_criteria'],
#                     verification_method=fsr_data['verification_method'],
#                     allocated_to=None,
#                     operating_modes="All modes"
#                 )
#                 all_fsrs.append(fsr_dict)
#         except (json.JSONDecodeError, KeyError) as e:
#             log.warning(f"Failed to parse FSRs for {goal_id}: {e}")
#             continue
    
#     # 4. Safety Mechanisms
#     log.info("Generating: safety_mechanisms")
#     fsr_list_text = "\n".join([f"- {fsr['id']}: {fsr['description']}" for fsr in all_fsrs])
    
#     sm_context = {
#         'fsr_list': fsr_list_text,
#         'goal_id': 'ALL',
#         'asil': 'D'
#     }
    
#     sm_prompt = template.get_prompt('safety_mechanisms', sm_context)
#     sm_response = cat.llm(sm_prompt)
    
#     try:
#         sm_response_clean = re.sub(r'```json\s*|\s*```', '', sm_response)
#         sm_json = json.loads(sm_response_clean)
        
#         for sm_data in sm_json:
#             # Use helper function
#             sm_dict = create_safety_mechanism_dict(
#                 id=sm_data['id'],
#                 name=sm_data.get('name', sm_data['id']),
#                 description=sm_data['description'],
#                 type=sm_data['type'],
#                 fsr_coverage=sm_data['fsr_coverage'],
#                 asil=sm_data['asil'],
#                 implementation=sm_data.get('implementation', 'TBD')
#             )
#             all_sms.append(sm_dict)
#     except (json.JSONDecodeError, KeyError) as e:
#         log.warning(f"Failed to parse safety mechanisms: {e}")
    
#     # 5. Architectural Allocation
#     log.info("Generating: architectural_allocation")
#     alloc_context = {
#         'num_fsrs': len(all_fsrs),
#         'architecture_description': architecture_desc
#     }
#     alloc_prompt = template.get_prompt('architectural_allocation', alloc_context)
#     architectural_allocation = cat.llm(alloc_prompt).strip()
    
#     # 6. Verification Strategy
#     log.info("Generating: verification_strategy")
#     asil_levels = list(set(fsr['asil'] for fsr in all_fsrs))
#     verif_context = {
#         'num_fsrs': len(all_fsrs),
#         'asil_levels': ', '.join(asil_levels)
#     }
#     verif_prompt = template.get_prompt('verification_strategy', verif_context)
#     verification_strategy = cat.llm(verif_prompt).strip()
    
#     # Create final structured content - PURE DICTIONARY
#     fsc_content = create_fsc_content_dict(
#         system_name=system_name,
#         introduction=introduction,
#         safety_goal_summary=safety_goal_summary,
#         functional_safety_requirements=all_fsrs,
#         safety_mechanisms=all_sms,
#         architectural_allocation=architectural_allocation,
#         verification_strategy=verification_strategy
#     )
    
#     # Validate before storing
#     is_valid, errors = validate_fsc_content(fsc_content)
#     if not is_valid:
#         log.warning(f"Generated content has validation issues: {errors}")
    
#     # Store in working memory - Just a dictionary!
#     cat.working_memory['fsc_structured_content'] = fsc_content
#     cat.working_memory['fsc_stage'] = 'structured_content_generated'
    
#     # Get statistics and format output
#     return format_fsc_summary(fsc_content) + """

# **Next Steps:**
# 1. Review content: `show fsc structured content`
# 2. Allocate FSRs: `allocate all FSRs`
# 3. Export documents: `create fsc word document` (in Output Formatter plugin)

# 💾 Structured content stored in working memory as 'fsc_structured_content'
# 📋 Contract version: 1.0"""