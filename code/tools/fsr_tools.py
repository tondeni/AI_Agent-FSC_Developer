# tools/fsr_tools.py
# FSR derivation tools - FIXED VERSION

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import sys
import os

plugin_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(plugin_folder)

from generators.fsr_generator import FSRGenerator
from core.models import SafetyGoal, SafetyStrategy, FunctionalSafetyRequirement
from core.validators import FSRValidator


@tool(
    return_direct=False,
    examples=[
        "derive FSRs for all goals",
        "derive functional safety requirements",
        "generate FSRs from safety goals"
    ]
)
def derive_functional_safety_requirements(tool_input, cat):
    """
    Derive Functional Safety Requirements from safety goals.
    
    Per ISO 26262-3:2018, Clause 7.4.2.
    Creates FSRs covering detection, control, warning, and other aspects.
    
    Input: "all goals" or specific goal ID like "SG-001"
    """
    
    log.info("✅ TOOL CALLED: derive_functional_safety_requirements")
    
    # Get data from working memory
    goals_data = cat.working_memory.get("fsc_safety_goals", [])
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    system_name = cat.working_memory.get("system_name", "the system")
    
    if not goals_data:
        # ✅ FIXED: Return string directly, not dict
        return "No safety goals loaded. Please load HARA first using: load HARA for [system name]"
    
    # Convert to model objects
    goals = [SafetyGoal(**g) for g in goals_data]
    strategies = [SafetyStrategy.from_dict(s) for s in strategies_data] if strategies_data else []
    
    # Filter for specific goal if requested
    tool_input_clean = str(tool_input).strip().upper()
    if "SG-" in tool_input_clean:
        sg_id = tool_input_clean.split("SG-")[1].split()[0]
        sg_id = f"SG-{sg_id}"
        goals = [g for g in goals if g.id == sg_id]
        
        if not goals:
            # ✅ FIXED: Return string directly
            return f"Safety goal {sg_id} not found in loaded HARA."
    
    log.info(f"📋 Deriving FSRs for {len(goals)} safety goals")
    
    try:
        # Get settings
        settings = cat.mad_hatter.get_plugin().load_settings()
        max_fsr_per_safety_goal = settings.get('max_fsr_per_safety_goal', 5)
        
        # Use generator for business logic
        generator = FSRGenerator(cat.llm, max_fsr_per_safety_goal)
        fsrs = generator.generate_fsrs(goals, strategies, max_fsr_per_safety_goal, system_name)
        
        if not fsrs:
            # ✅ FIXED: Return string directly
            return "Failed to generate FSRs. Please check safety goals and try again."
        
        # Validate FSRs
        validation_result = FSRValidator.validate_fsrs(fsrs, goals)
        
        if not validation_result.passed:
            log.warning("⚠️ FSR validation found issues")
        
        # Store in working memory
        cat.working_memory["fsc_functional_requirements"] = [f.to_dict() for f in fsrs]
        cat.working_memory["last_operation"] = "fsr_derivation"
        cat.working_memory["operation_timestamp"] = datetime.now().isoformat()
        
        # Calculate statistics
        total = len(fsrs)
        by_type = {}
        by_asil = {}
        
        for fsr in fsrs:
            by_type[fsr.type] = by_type.get(fsr.type, 0) + 1
            by_asil[fsr.asil] = by_asil.get(fsr.asil, 0) + 1
        
        # ✅ FIXED: Return string directly, not dict
        output = f"""✅ Successfully derived {total} Functional Safety Requirements

**System:** {system_name}
**Safety Goals Processed:** {len(goals)}

**FSR Distribution by ASIL:**
"""
        
        for asil in ['D', 'C', 'B', 'A', 'QM']:
            if asil in by_asil:
                output += f"- ASIL {asil}: {by_asil[asil]} FSRs\n"
        
        output += "\n**FSR Distribution by Type:**\n"
        for fsr_type, count in sorted(by_type.items()):
            output += f"- {fsr_type}: {count}\n"
        
        # Add validation info if issues found
        if validation_result.has_warnings():
            output += f"\n⚠️ Validation: {len(validation_result.warnings)} warnings"
        
        if validation_result.has_errors():
            output += f"\n❌ Validation: {len(validation_result.errors)} errors"
        
        output += "\n\n**Next Steps:**"
        output += "\n- Review FSRs: `show FSR summary`"
        output += "\n- Allocate FSRs: `allocate all FSRs`"
        output += "\n- Generate document: `generate FSC document`"
        
        log.info(f"✅ FSR derivation complete: {total} FSRs created")
        
        return output
        
    except Exception as e:
        log.error(f"❌ Error deriving FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        # ✅ FIXED: Return string directly
        return f"Error deriving FSRs: {str(e)}\n\nPlease check the logs for details."


@tool(
    return_direct=False,
    examples=[
        "show FSR summary",
        "list all FSRs",
        "show functional safety requirements"
    ]
)
def show_fsr_summary(tool_input, cat):
    """
    Show summary of all derived FSRs.
    Displays FSR distribution by type and ASIL level.
    """
    
    log.info("✅ TOOL CALLED: show_fsr_summary")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    system_name = cat.working_memory.get("system_name", "Unknown System")
    
    if not fsrs_data:
        # ✅ FIXED: Return string directly
        return "No FSRs derived yet. Use: derive FSRs for all goals"
    
    # Calculate statistics
    total = len(fsrs_data)
    by_type = {}
    by_asil = {}
    by_goal = {}
    allocated_count = 0
    
    for fsr in fsrs_data:
        # Count by type
        fsr_type = fsr.get('type', 'Unknown')
        by_type[fsr_type] = by_type.get(fsr_type, 0) + 1
        
        # Count by ASIL
        asil = fsr.get('asil', 'QM')
        by_asil[asil] = by_asil.get(asil, 0) + 1
        
        # Count by safety goal
        sg_id = fsr.get('safety_goal_id', 'Unknown')
        by_goal[sg_id] = by_goal.get(sg_id, 0) + 1
        
        # Count allocated
        if fsr.get('allocated_to') and fsr.get('allocated_to') != 'TBD':
            allocated_count += 1
    
    # ✅ FIXED: Return string directly
    output = f"""📊 **FSR Summary for {system_name}**

**Total FSRs:** {total}

**Distribution by ASIL:**
"""
    
    for asil in ['D', 'C', 'B', 'A', 'QM']:
        if asil in by_asil:
            output += f"- ASIL {asil}: {by_asil[asil]} FSRs\n"
    
    output += "\n**Distribution by Type:**\n"
    for fsr_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        output += f"- {fsr_type}: {count} FSRs\n"
    
    output += f"\n**Distribution by Safety Goal:**\n"
    for sg_id, count in sorted(by_goal.items()):
        output += f"- {sg_id}: {count} FSRs\n"
    
    output += f"\n**Allocation Status:** {allocated_count}/{total} FSRs allocated"
    
    output += "\n\n**Commands:**"
    output += "\n- View specific FSR: `show FSR FSR-SG-001-DET-1`"
    output += "\n- Allocate FSRs: `allocate all FSRs`"
    
    log.info(f"📊 Showed FSR summary: {total} FSRs")
    
    return output


@tool(
    return_direct=False,
    examples=[
        "show FSR FSR-SG-001-DET-1",
        "show details for FSR-001",
        "explain FSR-SG-002-CTL-1"
    ]
)
def show_fsr_details(tool_input, cat):
    """
    Show detailed information for a specific FSR.
    
    Input: FSR ID (e.g., "FSR-SG-001-DET-1")
    """
    
    log.info(f"✅ TOOL CALLED: show_fsr_details with input: {tool_input}")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs_data:
        # ✅ FIXED: Return string directly
        return "No FSRs available. Please derive FSRs first using: derive FSRs for all goals"
    
    # Parse FSR ID from input
    fsr_id = str(tool_input).strip().upper()
    fsr_id = fsr_id.replace("SHOW FSR", "").replace("SHOW", "").replace("FSR", "").strip()
    
    if not fsr_id.startswith('FSR-'):
        fsr_id = 'FSR-' + fsr_id
    
    # Find the FSR
    fsr_data = next((f for f in fsrs_data if f['id'] == fsr_id), None)
    
    if not fsr_data:
        available_ids = [f['id'] for f in fsrs_data[:5]]
        # ✅ FIXED: Return string directly
        return f"FSR '{fsr_id}' not found.\n\nAvailable FSRs: {', '.join(available_ids)}{'...' if len(fsrs_data) > 5 else ''}"
    
    # ✅ FIXED: Return string directly with formatted details
    output = f"""📋 **{fsr_id}** - {fsr_data.get('type', 'Unknown Type')}

**Description:**
{fsr_data.get('description', 'Not specified')}

**Safety Goal:** {fsr_data.get('safety_goal_id', 'Unknown')}
*{fsr_data.get('safety_goal', 'Not specified')}*

**ASIL Level:** {fsr_data.get('asil', 'QM')}

**Allocated To:** {fsr_data.get('allocated_to', 'TBD')}

**Verification Criteria:**
{fsr_data.get('verification_criteria', 'Not specified')}

**Timing Requirements:** {fsr_data.get('timing', 'Not specified')}

**Safe State:** {fsr_data.get('safe_state', 'Not specified')}

**Operating Modes:** {fsr_data.get('operating_modes', 'All modes')}
"""
    
    log.info(f"📋 Showed details for {fsr_id}")
    
    return output


@tool(
    return_direct=False,
    examples=[
        "list FSRs for SG-001",
        "show FSRs for safety goal 1",
        "what FSRs are linked to SG-002"
    ]
)
def list_fsrs_for_goal(tool_input, cat):
    """
    List all FSRs for a specific safety goal.
    
    Input: Safety goal ID (e.g., "SG-001")
    """
    
    log.info(f"✅ TOOL CALLED: list_fsrs_for_goal with input: {tool_input}")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
    if not fsrs_data:
        # ✅ FIXED: Return string directly
        return "No FSRs available. Please derive FSRs first."
    
    # Parse safety goal ID
    sg_id = str(tool_input).strip().upper()
    sg_id = sg_id.replace("FOR", "").replace("GOAL", "").replace("SAFETY", "").strip()
    
    if not sg_id.startswith('SG-'):
        sg_id = 'SG-' + sg_id.replace('SG', '').replace('-', '').strip()
    
    # Find matching FSRs
    matching_fsrs = [f for f in fsrs_data if f.get('safety_goal_id') == sg_id]
    
    if not matching_fsrs:
        # ✅ FIXED: Return string directly
        return f"No FSRs found for safety goal {sg_id}."
    
    # Find the safety goal info
    goal_info = next((g for g in goals_data if g.get('id') == sg_id), None)
    
    # ✅ FIXED: Return string directly
    output = f"""📋 **FSRs for {sg_id}**

"""
    
    if goal_info:
        output += f"**Safety Goal:** {goal_info.get('description', 'Not specified')}\n"
        output += f"**ASIL:** {goal_info.get('asil', 'Unknown')}\n\n"
    
    output += f"**Total FSRs:** {len(matching_fsrs)}\n\n"
    
    # Group by type
    by_type = {}
    for fsr in matching_fsrs:
        fsr_type = fsr.get('type', 'Unknown')
        if fsr_type not in by_type:
            by_type[fsr_type] = []
        by_type[fsr_type].append(fsr)
    
    for fsr_type, fsrs in sorted(by_type.items()):
        output += f"**{fsr_type}:**\n"
        for fsr in fsrs:
            output += f"- {fsr['id']}: {fsr.get('description', 'Not specified')[:80]}...\n"
        output += "\n"
    
    log.info(f"📋 Listed {len(matching_fsrs)} FSRs for {sg_id}")
    
    return output