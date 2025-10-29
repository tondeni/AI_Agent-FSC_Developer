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
        "generate FSRs from safety goals",
        "derive FSRs"
    ]
)
def derive_functional_safety_requirements(tool_input, cat):
    """
    Use this tool to derive Functional Safety Requirements (FSRs) from loaded safety goals.
    
    This tool MUST be used when the user asks to derive, create or generate functional safety requirements or FSRs    
    Per ISO 26262-3:2018, Clause 7.4.2.
    
    Input: "all goals" to process all goals, or specific goal ID like "SG-001"
    
    Prerequisites: Safety goals must be loaded first using the load_hara tool.
    """
    
    log.warning(f"----------------✅ TOOL CALLED: derive_functional_safety_requirements with input: {tool_input}")
    
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
        cat.working_memory.fsc_functional_requirements = [f.to_dict() for f in fsrs]
        cat.working_memory.last_operation = "fsr_derivation"
        cat.working_memory.fsc_stage = "fsrs_derived"
        cat.working_memory.operation_timestamp = datetime.now().isoformat()
        
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
        "show functional safety requirements",
        "show all FSRs",
        "display FSR overview",
        "what FSRs do we have",
        "FSR summary",
        "show me the FSRs",
        "list functional safety requirements",
        "display all FSRs",
        "show FSR statistics",
        "FSR overview"
    ]
)
def show_fsr_summary(tool_input, cat):
    """
    Use this tool to show a summary of all derived Functional Safety Requirements (FSRs).
    
    This tool MUST be used when the user asks to:
    - show FSR summary
    - list all FSRs
    - display FSRs
    - view FSR overview
    - see FSR statistics
    - show functional safety requirements
    - get FSR information
    
    The tool displays:
    - Total number of FSRs
    - Distribution by ASIL level (D, C, B, A, QM)
    - Distribution by FSR type (Detection, Control, Warning, etc.)
    - Distribution by Safety Goal
    - Allocation status
    
    Prerequisites: FSRs must be derived first using derive_functional_safety_requirements tool.
    
    Input: Not required (can be empty or "all" or "summary")
    """
    
    log.warning(f"----------------✅ TOOL CALLED: show_fsr_summary with input: {tool_input}")
    
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
        "explain FSR-SG-002-CTL-1",
        "what is FSR-SG-001-DET-1",
        "show me FSR-001",
        "display FSR FSR-SG-003-WRN-1",
        "details of FSR-SG-001-CTL-2",
        "explain FSR 001",
        "show FSR details for FSR-SG-002-DET-1",
        "get information about FSR-001",
        "tell me about FSR-SG-001-DET-1"
    ]
)
def show_fsr_details(tool_input, cat):
    """
    Use this tool to show detailed information for a specific Functional Safety Requirement (FSR).
    
    This tool MUST be used when the user asks to:
    - show FSR details
    - explain a specific FSR
    - display FSR information
    - show FSR [ID]
    - what is FSR-[ID]
    - get details about FSR-[ID]
    - tell me about FSR-[ID]
    
    The tool displays complete FSR information including:
    - FSR ID and type
    - Full description
    - Linked Safety Goal
    - ASIL level
    - Allocation target (HW/SW component)
    - Verification criteria
    - Timing requirements (FTTI)
    - Safe state definition
    - Operating modes
    
    Prerequisites: FSRs must be derived first.
    
    Input: FSR ID in format "FSR-SG-XXX-YYY-Z" (e.g., "FSR-SG-001-DET-1")
    The tool accepts various formats:
    - "FSR-SG-001-DET-1"
    - "FSR-001-DET-1" 
    - "001-DET-1"
    - "SG-001-DET-1"
    """
    
    log.warning(f"----------------✅ TOOL CALLED: show_fsr_details with input: {tool_input}")
    
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
    
    log.warning(f"----------------✅ TOOL CALLED: list_fsrs_for_goal with input: {tool_input}")
    
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


@tool(
    return_direct=False,
    examples=[
        "generate structured FSC content",
        "create complete FSC with templates",
        "build FSC using templates"
    ]
)
def generate_structured_fsc_content(tool_input, cat):
    """
    Generate complete, structured FSC content using template-based approach.
    
    Output is stored as pure dictionary in working memory - no classes needed.
    Contract-based: Output Formatter can read this without importing anything.
    
    Prerequisites:
    - Safety goals must be loaded (from HARA)
    
    Input: Not needed
    """
    # IMPORTANT ***
    # Input: system architecture description when available 
    log.warning(f"----------------✅ TOOL CALLED: generate_structured_fsc_content with input: {tool_input}")
    
    # Import only local helpers
    import sys
    import os
    code_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, code_folder)
    
    from models.fsc_templates import FSCContentTemplate
    from models.fsc_content_models import (
        create_fsr_dict,
        create_safety_mechanism_dict,
        create_fsc_content_dict,
        validate_fsc_content,
        get_fsc_statistics,
        format_fsc_summary
    )
    import json
    import re
    
    # Get prerequisites
    goals_data = cat.working_memory.get("fsc_safety_goals", [])
    system_name = cat.working_memory.get("system_name", "Unknown System")
    architecture_desc = tool_input.strip() if tool_input.strip() else "To be defined"
    
    if not goals_data:
        return """❌ No safety goals loaded. 

**Required:**
1. Load HARA: `load HARA for [system]`

Then retry: `generate structured FSC content`"""
    
    # Initialize template
    template = FSCContentTemplate()
    
    # Prepare context
    goals_list = "\n".join([
        f"- {g.get('id', 'SG-?')}: {g.get('goal', 'Unknown')} (ASIL {g.get('asil', '?')})"
        for g in goals_data
    ])
    
    # Collect generated content
    introduction = ""
    safety_goal_summary = ""
    all_fsrs = []
    all_sms = []
    architectural_allocation = ""
    verification_strategy = ""
    
    log.info(f"📝 Generating structured FSC for {system_name}")
    
    # 1. Introduction
    log.info("Generating: introduction")
    intro_context = {
        'item_name': system_name,
        'item_context': f"System with {len(goals_data)} safety goals requiring FSC per ISO 26262-3:2018"
    }
    intro_prompt = template.get_prompt('introduction', intro_context)
    introduction = cat.llm(intro_prompt).strip()
    
    # 2. Safety Goal Summary
    log.info("Generating: safety_goal_summary")
    sg_context = {'safety_goals_list': goals_list}
    sg_prompt = template.get_prompt('safety_goal_summary', sg_context)
    safety_goal_summary = cat.llm(sg_prompt).strip()
    
    # 3. FSRs (per goal)
    log.info("Generating: FSRs")
    
    # Get strategies - handle both dict and list formats
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    
    for goal in goals_data:
        goal_id = goal.get('id', 'SG-?')
        
        # Handle both dict (keyed by goal_id) and list formats
        if isinstance(strategies_data, dict):
            goal_strategies = strategies_data.get(goal_id, {})
        elif isinstance(strategies_data, list):
            # Filter strategies for this goal from list
            goal_strategies = [s for s in strategies_data if s.get('safety_goal_id') == goal_id]
        else:
            goal_strategies = {}
        
        strategies_text = json.dumps(goal_strategies, indent=2) if goal_strategies else "Standard strategies per ISO 26262-3"
        
        fsr_context = {
            'safety_goal': goal.get('goal', ''),
            'asil': goal.get('asil', 'QM'),
            'goal_id': goal_id.replace('SG-', ''),
            'strategies': strategies_text
        }
        
        fsr_prompt = template.get_prompt('functional_safety_requirements', fsr_context)
        fsr_response = cat.llm(fsr_prompt)
        
        # Parse JSON
        try:
            fsr_response_clean = re.sub(r'```json\s*|\s*```', '', fsr_response)
            fsr_json = json.loads(fsr_response_clean)
            
            for fsr_data in fsr_json:
                # Use helper function to create FSR dict
                fsr_dict = create_fsr_dict(
                    id=fsr_data['id'],
                    description=fsr_data['description'],
                    type=fsr_data['type'],
                    asil=fsr_data['asil'],
                    safety_goal_id=goal_id,
                    safe_state=fsr_data['safe_state'],
                    ftti=fsr_data['ftti'],
                    validation_criteria=fsr_data['validation_criteria'],
                    verification_method=fsr_data['verification_method'],
                    allocated_to=None,
                    operating_modes="All modes"
                )
                all_fsrs.append(fsr_dict)
        except (json.JSONDecodeError, KeyError) as e:
            log.warning(f"Failed to parse FSRs for {goal_id}: {e}")
            continue
    
    # 4. Safety Mechanisms
    log.info("Generating: safety_mechanisms")
    fsr_list_text = "\n".join([f"- {fsr['id']}: {fsr['description']}" for fsr in all_fsrs])
    
    sm_context = {
        'fsr_list': fsr_list_text,
        'goal_id': 'ALL',
        'asil': 'D'
    }
    
    sm_prompt = template.get_prompt('safety_mechanisms', sm_context)
    sm_response = cat.llm(sm_prompt)
    
    try:
        sm_response_clean = re.sub(r'```json\s*|\s*```', '', sm_response)
        sm_json = json.loads(sm_response_clean)
        
        for sm_data in sm_json:
            # Use helper function
            sm_dict = create_safety_mechanism_dict(
                id=sm_data['id'],
                name=sm_data.get('name', sm_data['id']),
                description=sm_data['description'],
                type=sm_data['type'],
                fsr_coverage=sm_data['fsr_coverage'],
                asil=sm_data['asil'],
                implementation=sm_data.get('implementation', 'TBD')
            )
            all_sms.append(sm_dict)
    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"Failed to parse safety mechanisms: {e}")
    
    # 5. Architectural Allocation
    log.info("Generating: architectural_allocation")
    alloc_context = {
        'num_fsrs': len(all_fsrs),
        'architecture_description': architecture_desc
    }
    alloc_prompt = template.get_prompt('architectural_allocation', alloc_context)
    architectural_allocation = cat.llm(alloc_prompt).strip()
    
    # 6. Verification Strategy
    log.info("Generating: verification_strategy")
    asil_levels = list(set(fsr['asil'] for fsr in all_fsrs))
    verif_context = {
        'num_fsrs': len(all_fsrs),
        'asil_levels': ', '.join(asil_levels)
    }
    verif_prompt = template.get_prompt('verification_strategy', verif_context)
    verification_strategy = cat.llm(verif_prompt).strip()
    
    # Create final structured content - PURE DICTIONARY
    fsc_content = create_fsc_content_dict(
        system_name=system_name,
        introduction=introduction,
        safety_goal_summary=safety_goal_summary,
        functional_safety_requirements=all_fsrs,
        safety_mechanisms=all_sms,
        architectural_allocation=architectural_allocation,
        verification_strategy=verification_strategy
    )
    
    # Validate before storing
    is_valid, errors = validate_fsc_content(fsc_content)
    if not is_valid:
        log.warning(f"Generated content has validation issues: {errors}")
    
    # Store in working memory - Just a dictionary!
    cat.working_memory['fsc_structured_content'] = fsc_content
    cat.working_memory['fsc_stage'] = 'structured_content_generated'
    
    # Get statistics and format output
    return format_fsc_summary(fsc_content) + """

**Next Steps:**
1. Review content: `show fsc structured content`
2. Allocate FSRs: `allocate all FSRs`
3. Export documents: `create fsc word document` (in Output Formatter plugin)

💾 Structured content stored in working memory as 'fsc_structured_content'
📋 Contract version: 1.0"""