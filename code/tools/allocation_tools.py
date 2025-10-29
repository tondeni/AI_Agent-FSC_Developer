# ==============================================================================
# tools/allocation_tools.py (REFINED VERSION)
# Tools for FSR allocation following FSR tool pattern
# ==============================================================================

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import sys
import os

plugin_folder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(plugin_folder)

from generators.allocation_generator import AllocationGenerator, AllocationAnalyzer
from core.models import FunctionalSafetyRequirement, SafetyGoal


@tool(
    return_direct=False,
    examples=[
        "allocate FSRs",
        "allocate functional safety requirements to system elements",
        "allocate FSRs to architecture"
    ]
)
def allocate_functional_requirements(tool_input, cat):
    """ALLOCATION ACTION TOOL: Performs automatic allocation of FSRs to architectural elements.
    
    Use ONLY when user wants to START THE ALLOCATION PROCESS for multiple FSRs.
    This tool assigns FSRs to system components/elements.
    
    Trigger phrases: "allocate FSRs", "allocate all FSRs", "start allocation"
    NOT for: viewing allocations, manual single allocation, or allocation summaries
    
    Action: Analyzes FSRs and allocates them to architectural components
    Prerequisites: FSRs must be derived first
    ISO Reference: ISO 26262-3:2018, Clause 7.4.2.8
    Input: Not required
    """

    log.warning("----------------✅ TOOL CALLED: allocate_functional_requirements ----------------- ")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    goals_data = cat.working_memory.get("fsc_safety_goals", [])
    system_name = cat.working_memory.get("system_name", "the system")
    
    if not fsrs_data:
        return "No FSRs available to allocate. Please derive FSRs first using: derive FSRs for all goals"
    
    # Convert to objects
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    goals = [SafetyGoal(**g) for g in goals_data] if goals_data else []
    
    log.info(f"📋 Allocating {len(fsrs)} FSRs to architectural elements")
    
    try:
        # Use generator for allocation logic
        generator = AllocationGenerator(cat.llm)
        allocated_fsrs = generator.allocate_fsrs(fsrs, goals, system_name)
        
        # Store updated FSRs
        cat.working_memory["fsc_functional_requirements"] = [f.to_dict() for f in allocated_fsrs]
        cat.working_memory["last_operation"] = "fsr_allocation"
        cat.working_memory.fsc_stage = "fsrs_allocated"
        cat.working_memory["operation_timestamp"] = datetime.now().isoformat()
        
        # Get allocation statistics
        stats = AllocationAnalyzer.get_allocation_statistics(allocated_fsrs)
        
        # Simple output - let agent format details
        output = f"""✅ Successfully allocated {stats['allocated']} of {stats['total_fsrs']} FSRs"""
      
        log.info(f"✅ Allocation complete: {stats['allocated']}/{stats['total_fsrs']} FSRs allocated")
        
        # Ensure TOOL string return
        return str(output)
        
    except Exception as e:
        log.error(f"❌ Error allocating FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"Error during allocation: {str(e)}\n\nPlease check the logs for details."


@tool(
    return_direct=False,
    examples=[
        "show allocation summary",
        "allocation overview",
        "FSR allocation status",
        "show how FSRs are allocated"
    ]
)
def show_allocation_summary(tool_input, cat):
    """DISPLAY TOOL: Shows allocation summary grouped by components.
    
    Use when user wants to VIEW ALLOCATION STATISTICS and component groupings.
    Shows which components have FSRs and allocation coverage.
    
    Trigger phrases: "show allocation summary", "allocation overview"
    NOT for: performing allocation, allocation matrix, or single FSR allocation
    
    Displays: FSRs grouped by component, allocation statistics, ASIL distribution
    Prerequisites: FSRs should be allocated
    Input: Not required
    """
    
    log.warning("----------------✅ TOOL CALLED: show_allocation_summary ----------------")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    system_name = cat.working_memory.get("system_name", "the system")
    
    if not fsrs_data:
        return "No FSRs available. Please derive FSRs first using: derive FSRs for all goals"
    
    # Convert to objects for analysis
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    
    # Get statistics
    stats = AllocationAnalyzer.get_allocation_statistics(fsrs)
    
    # Build summary
    output = f"""📊 **FSR Allocation Summary for {system_name}**

**Total FSRs:** {stats['total']}
**Allocated:** {stats['allocated']} ({stats['allocated']*100//stats['total'] if stats['total'] > 0 else 0}%)
**Unallocated:** {stats['unallocated']}

---

## Allocation by Component Type

"""
    
    for comp_type, count in sorted(stats['by_component_type'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['allocated'] * 100) if stats['allocated'] > 0 else 0
        output += f"**{comp_type}:** {count} FSRs ({percentage:.1f}%)\n"
    
    output += "\n---\n\n## Allocation by Component\n\n"
    
    # Show top components
    sorted_components = sorted(stats['by_component'].items(), 
                               key=lambda x: x[1]['count'], 
                               reverse=True)
    
    for component, info in sorted_components[:10]:  # Show top 10
        asil_str = ', '.join(sorted(info['asil_levels'], reverse=True))
        output += f"### {component}\n"
        output += f"- FSRs: {info['count']}\n"
        output += f"- ASIL Levels: {asil_str}\n"
        output += f"- FSR IDs: {', '.join(info['fsr_ids'][:3])}"
        if len(info['fsr_ids']) > 3:
            output += f" ... (+{len(info['fsr_ids']) - 3} more)"
        output += "\n\n"
    
    if len(sorted_components) > 10:
        output += f"*... and {len(sorted_components) - 10} more components*\n\n"
    
    output += "---\n\n## ASIL Distribution\n\n"
    
    for asil in ['D', 'C', 'B', 'A', 'QM']:
        if asil in stats['by_asil']:
            output += f"- ASIL {asil}: {stats['by_asil'][asil]} FSRs\n"
    
    output += "\n**Commands:**"
    output += "\n- View specific FSR: `show FSR FSR-SG-001-DET-1`"
    output += "\n- Manually allocate: `allocate FSR-001 to Component Name`"
    
    log.info(f"📊 Showed allocation summary: {stats['allocated']}/{stats['total']} allocated")
    
    # Ensure tool string return
    return str(output)


@tool(
    return_direct=False,
    examples=[
        "show allocation matrix",
        "generate allocation matrix table",
        "allocation traceability matrix"
    ]
)
def show_allocation_matrix(tool_input, cat):
    """MATRIX TOOL: Generates detailed traceability allocation matrix table.
    
    Use when user specifically requests an ALLOCATION MATRIX or TRACEABILITY TABLE.
    Shows Safety Goals → FSRs → Components mapping in table format.
    
    Trigger phrases: "show allocation matrix", "allocation table", "traceability matrix"
    NOT for: allocation summary, performing allocation, or statistics
    
    Displays: Complete matrix with SG → FSR → Component traceability
    ISO Reference: ISO 26262-3:2018, Clause 7.4.2.8
    Input: Not required
    """

    log.warning("----------------✅ TOOL CALLED: show_allocation_matrix ----------------")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    system_name = cat.working_memory.get("system_name", "the system")
    
    if not fsrs_data:
        return "No FSRs available. Please derive and allocate FSRs first."
    
    # Convert to objects
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    
    # Use analyzer to format matrix
    matrix = AllocationAnalyzer.format_allocation_matrix(fsrs)
    
    # Add header
    output = f"""# FSR Allocation Matrix
**System:** {system_name}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

*ISO 26262-3:2018, Clause 7.4.2.8 - FSR Allocation to Architectural Elements*

---

{matrix}

---

## Allocation Validation

"""
    
    # Validate allocation
    is_valid, issues = AllocationAnalyzer.validate_allocation(fsrs)
    
    if is_valid:
        output += "✅ **Allocation Status:** Complete and valid\n"
    else:
        output += "⚠️ **Allocation Issues Found:**\n\n"
        for issue in issues:
            output += f"- {issue}\n"
    
    output += "\n**Next Steps:**"
    output += "\n- Specify validation criteria: `specify validation criteria`"
    output += "\n- Verify FSC: `verify FSC`"
    
    return str(output)


@tool(
    return_direct=False,
    examples=[
        "allocate FSR-SG-001-DET-1 to Battery Monitor",
        "manually allocate FSR-001 to Safety Controller",
        "assign FSR-002 to Voltage Sensor"
    ]
)
def allocate_single_fsr(tool_input, cat):
    """MANUAL ALLOCATION TOOL: Manually allocates ONE SPECIFIC FSR to a component.
    
    Use ONLY when user wants to MANUALLY ASSIGN a SINGLE FSR using its ID.
    
    Trigger phrases: "allocate FSR-XXX to Component", "assign FSR-YYY to..."
    NOT for: automatic allocation, viewing allocations, or multiple FSRs
    
    Action: Assigns one FSR to specified component with rationale
    Prerequisites: FSRs must be derived
    Input: REQUIRED - Format "FSR-ID to Component Name"
    Example: "FSR-SG-001-DET-1 to Battery Monitor"
    """
    log.warning(f"----------------✅ TOOL CALLED: allocate_single_fsr with input: {tool_input} ----------------")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs_data:
        return "No FSRs available. Please derive FSRs first using: derive FSRs for all goals"
    
    # Parse input
    input_str = str(tool_input).upper()
    
    if " TO " not in input_str:
        return "Invalid format. Use: 'FSR-ID to Component Name'\n\nExample: allocate FSR-SG-001-DET-1 to Battery Monitor"
    
    parts = input_str.split(" TO ")
    fsr_id = parts[0].strip()
    component = parts[1].strip().title()
    
    # Clean up FSR ID
    fsr_id = fsr_id.replace("ALLOCATE", "").replace("FSR", "").strip()
    if not fsr_id.startswith("FSR-"):
        fsr_id = "FSR-" + fsr_id
    
    # Find FSR
    fsr_data = next((f for f in fsrs_data if f['id'] == fsr_id), None)
    
    if not fsr_data:
        available_ids = [f['id'] for f in fsrs_data[:5]]
        return f"FSR '{fsr_id}' not found.\n\nAvailable FSRs: {', '.join(available_ids)}{'...' if len(fsrs_data) > 5 else ''}"
    
    # Create FSR object for allocation
    fsr = FunctionalSafetyRequirement(**fsr_data)
    
    # Use generator for proper allocation
    generator = AllocationGenerator(cat.llm)
    allocated_fsr = generator.allocate_single_fsr(fsr, component)
    
    # Update in working memory
    for i, f in enumerate(fsrs_data):
        if f['id'] == fsr_id:
            fsrs_data[i] = allocated_fsr.to_dict()
            break
    
    cat.working_memory["fsc_functional_requirements"] = fsrs_data
    
    # Build output
    output = f"""✅ **FSR Allocated Successfully**"""

# **FSR:** {fsr_id}
# **Description:** {fsr_data.get('description', 'Not specified')[:80]}...
# **ASIL:** {fsr_data.get('asil', 'QM')}
# **Type:** {fsr_data.get('type', 'Unknown')}

# **Allocated To:** {component}
# **Component Type:** {allocated_fsr.allocation_type}
# **Rationale:** {allocated_fsr.allocation_rationale}

# ---

# **Allocation Status:** Updated in working memory
# **View Summary:** `show allocation summary`
# """
    
#     log.info(f"✅ Manual allocation: {fsr_id} → {component}")
    
    return str(output)


@tool(
    return_direct=False,
    examples=[
        "list FSRs for Battery Monitor",
        "show FSRs allocated to Safety Controller",
        "FSRs for component Voltage Sensor"
    ]
)
def list_fsrs_by_component(tool_input, cat):
    """FILTER TOOL: Lists FSRs filtered by a SPECIFIC COMPONENT name.
    
    Use when user wants to see ALL FSRs assigned to ONE PARTICULAR COMPONENT.
    
    Trigger phrases: "FSRs for [Component]", "FSRs allocated to [Component]"
    NOT for: allocation summary, all FSRs, or single FSR details
    
    Displays: All FSRs for one component, grouped by ASIL
    Prerequisites: FSRs should be allocated
    Input: REQUIRED - Component name like "Battery Monitor"
    """
    
    log.warning(f"----------------✅ TOOL CALLED: list_fsrs_by_component with input: {tool_input} ----------------")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs_data:
        return "No FSRs available. Please derive and allocate FSRs first."
    
    # Parse component name from input
    component_name = str(tool_input).lower()
    component_name = component_name.replace("list fsrs for", "").replace("fsrs for", "").replace("for", "").strip().title()
    
    # Find matching FSRs (case-insensitive partial match)
    matching_fsrs = []
    for fsr in fsrs_data:
        allocated = fsr.get('allocated_to', '').lower()
        if component_name.lower() in allocated or allocated in component_name.lower():
            matching_fsrs.append(fsr)
    
    if not matching_fsrs:
        return f"No FSRs found allocated to '{component_name}'.\n\nUse `show allocation summary` to see all components."
    
    # Build output
    output = f"""📋 **FSRs Allocated to: {component_name}**

**Total FSRs:** {len(matching_fsrs)}

---

"""
    
    # Group by ASIL
    by_asil = {}
    for fsr in matching_fsrs:
        asil = fsr.get('asil', 'QM')
        if asil not in by_asil:
            by_asil[asil] = []
        by_asil[asil].append(fsr)
    
    for asil in ['D', 'C', 'B', 'A', 'QM']:
        if asil in by_asil:
            output += f"## ASIL {asil} ({len(by_asil[asil])} FSRs)\n\n"
            
            for fsr in by_asil[asil]:
                output += f"### {fsr['id']}\n"
                output += f"**Type:** {fsr.get('type', 'Unknown')}\n"
                output += f"**Description:** {fsr.get('description', 'Not specified')}\n"
                output += f"**Safety Goal:** {fsr.get('safety_goal_id', 'Unknown')}\n"
                if fsr.get('allocation_rationale'):
                    output += f"**Rationale:** {fsr['allocation_rationale']}\n"
                output += "\n"
    
    output += "---\n\n"
    output += "**View Details:** `show FSR FSR-SG-XXX-YYY-Z`\n"
    output += "**Allocation Summary:** `show allocation summary`\n"
    
    log.info(f"📋 Listed {len(matching_fsrs)} FSRs for component: {component_name}")
    
    return str(output)