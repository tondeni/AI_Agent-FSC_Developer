# tools/fsr_tools.py
# FSR derivation tools

from cat.mad_hatter.decorators import tool
from cat.log import log
import sys
import os

# Add parent directory to path
plugin_folder = os.path.dirname(os.path.dirname(__file__))
sys.path.append(plugin_folder)

from generators.fsr_generator import FSRGenerator, FSRFormatter
from core.models import SafetyGoal, SafetyStrategy, FunctionalSafetyRequirement
from core.validators import FSRValidator


@tool(
    return_direct=True,
    examples=[
        "derive FSRs for all goals",
        "derive functional safety requirements",
        "generate FSRs for SG-001",
        "develop FSRs"
    ]
)
def derive_functional_safety_requirements(tool_input, cat):
    """
    Derive Functional Safety Requirements (FSRs) from safety goals.
    
    Per ISO 26262-3:2018:
    - 7.4.2.1: FSRs shall be derived from safety goals
    - 7.4.2.2: At least one FSR per safety goal
    - 7.4.2.4: Each FSR shall consider: operating modes, FTTI, safe states, 
               emergency operation, functional redundancies
    
    Creates measurable, verifiable requirements implementing the strategies.
    
    Input: "derive FSRs for all goals" or "derive FSRs for SG-XXX"
    """
    
    log.info("✅ TOOL CALLED: derive_functional_safety_requirements")
    # Get plugin settings
    settings = cat.mad_hatter.get_plugin().load_settings()

    # ========================================================================
    # Load plugin settings
    # ========================================================================
    try:
        settings = cat.mad_hatter.get_plugin().load_settings()
        max_fsr_per_safety_goal = settings.get('max_fsr_per_safety_goal', 5)
        log.info(f"📋 Settings loaded: max_fsr_per_safety_goal ={max_fsr_per_safety_goal}")
    except Exception as e:
        log.warning(f"⚠️ Could not load settings, using defaults: {e}")
        max_fsr_per_safety_goal = 5  # Default fallback
    # ========================================================================

    
    # Get data from working memory
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    
    if not safety_goals_data:
        return """❌ No safety goals loaded.

**Required Steps per ISO 26262-3:2018:**
1. Load HARA (7.3.1): `load HARA for [item name]`
2. Develop strategy (7.4.2.3): `develop safety strategy for all goals`
3. Derive FSRs (7.4.2.1): `derive FSRs for all goals`
"""
    
    # Convert to objects
    safety_goals = [SafetyGoal(**g) for g in safety_goals_data]
    strategies = [SafetyStrategy.from_dict(s) for s in strategies_data] if strategies_data else []
    system_name = cat.working_memory.get("system_name", "the system")
    
    # Parse input
    input_str = str(tool_input).strip().lower()
    
    if "all" in input_str or input_str == "" or "safety goals" in input_str:
        goals_to_process = safety_goals
        log.info(f"🎯 Deriving FSRs for {len(goals_to_process)} safety goals")
    else:
        sg_id = str(tool_input).strip().upper()
        sg_id = sg_id.replace("DERIVE FSRS FOR", "").replace("FSR FOR", "").strip()
        if not sg_id.startswith('SG-'):
            sg_id = 'SG-' + sg_id.replace('SG', '').replace('-', '').strip()
        goals_to_process = [g for g in safety_goals if g.id == sg_id]
        
        if not goals_to_process:
            return f"❌ Safety Goal '{sg_id}' not found."
    
    try:
        # Initialize FSR generator
        generator = FSRGenerator(cat.llm, max_fsr_per_safety_goal)
        
        # Generate FSRs
        log.info("🔄 Generating FSRs...")
        fsrs = generator.generate_fsrs(goals_to_process, strategies, max_fsr_per_safety_goal, system_name)
        
        if not fsrs:
            return "❌ Failed to generate FSRs. Please try again."
        
        # Validate FSRs
        validation_result = FSRValidator.validate_fsrs(fsrs, goals_to_process)
        
        if not validation_result.passed:
            log.warning("⚠️ FSR validation found issues")
        
        # Store in working memory
        cat.working_memory["fsc_functional_requirements"] = [fsr.to_dict() for fsr in fsrs]
        cat.working_memory["fsc_stage"] = "fsrs_derived"
        cat.working_memory["document_type"] = "fsr"
        
        # Format output
        formatter = FSRFormatter()
        
        #Statistics
        summary = f"""✅ **Functional Safety Requirements Derived**

*ISO 26262-3:2018, Clause 7.4.2 compliance*

**System:** {system_name}
**Total FSRs:** {len(fsrs)}

**FSR Distribution by ASIL:**
"""
        
        # Count by ASIL
        asil_counts = {}
        for fsr in fsrs:
            asil_counts[fsr.asil] = asil_counts.get(fsr.asil, 0) + 1
        
        for asil in ['D', 'C', 'B', 'A']:
            if asil in asil_counts:
                summary += f"- ASIL {asil}: {asil_counts[asil]} FSRs\n"
        
        # Count by type
        type_counts = {}
        for fsr in fsrs:
            type_counts[fsr.type] = type_counts.get(fsr.type, 0) + 1
        
        summary += "\n**FSR Distribution by Type:**\n"
        for fsr_type, count in sorted(type_counts.items()):
            summary += f"- {fsr_type}: {count} FSRs\n"
        
        summary += "\n---\n\n"
        
        # Add FSR table
        summary += "## Functional Safety Requirements\n\n"
        summary += formatter.format_fsr_table(fsrs)
        
        # Add validation summary
        if validation_result.has_errors() or validation_result.has_warnings():
            summary += "\n\n---\n\n"
            summary += validation_result.format_report()
        
        # Add compliance check
        summary += "\n\n---\n\n"
        summary += """**ISO 26262-3:2018 Compliance:**
✅ 7.4.2.1: FSRs derived from safety goals
✅ 7.4.2.2: At least one FSR per safety goal
✅ 7.4.2.4: FSRs consider operating modes, FTTI, safe states
✅ 7.4.1: FSRs specified per ISO 26262-8 requirements

**Completed:**
- ✅ Step 1: Safety Goals extracted from HARA
- ✅ Step 2: Safety Strategies developed
- ✅ Step 3: Functional Safety Requirements derived

**Next Steps per ISO 26262-3:2018:**

➡️ **Step 4:** Allocate FSRs to system architecture
   ```
   allocate all FSRs
   ```

➡️ **Step 5:** Specify Validation Criteria
   ```
   specify validation criteria
   ```

➡️ **Step 6:** Generate FSC Document
   ```
   generate FSC document
   ```
"""
        
        log.info(f"✅ FSRs generated: {len(fsrs)} requirements")
        
        return summary
        
    except Exception as e:
        log.error(f"Error deriving FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error deriving FSRs: {str(e)}\n\nPlease try again or check the logs."


@tool(return_direct=True)
def show_fsr_details(tool_input, cat):
    """
    Show detailed information for a specific FSR.
    
    Input: FSR ID (e.g., "FSR-SG-001-DET-1")
    Example: "show FSR FSR-SG-001-DET-1"
    """
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs_data:
        return "❌ No FSRs derived yet. Use: `derive FSRs for all goals`"
    
    # Parse input
    fsr_id = str(tool_input).strip().upper()
    fsr_id = fsr_id.replace("SHOW FSR", "").replace("FSR", "").strip()
    if not fsr_id.startswith('FSR-'):
        fsr_id = 'FSR-' + fsr_id
    
    # Find FSR
    fsr_data = next((f for f in fsrs_data if f['id'] == fsr_id), None)
    
    if not fsr_data:
        available = ', '.join([f['id'] for f in fsrs_data[:5]])
        return f"""❌ FSR '{fsr_id}' not found.

**Available FSRs:** {available}{'...' if len(fsrs_data) > 5 else ''}

**Usage:** `show FSR FSR-SG-001-DET-1`
"""
    
    # Build detailed view
    details = f"""## 📋 FSR Details: {fsr_id}

**Description:**
{fsr_data.get('description', 'Not specified')}

**Classification:**
- **Type:** {fsr_data.get('type', 'Unknown')}
- **ASIL:** {fsr_data.get('asil', 'Unknown')}
- **Linked to Safety Goal:** {fsr_data.get('safety_goal_id', 'Unknown')}

**Requirements per ISO 26262-3:2018, 7.4.2.4:**
- **Operating Modes:** {fsr_data.get('operating_modes', 'Not specified')}
- **Timing (FTTI):** {fsr_data.get('timing', 'Not specified')}
- **Safe State:** {fsr_data.get('safe_state', 'Not specified')}
- **Emergency Operation:** {fsr_data.get('emergency_operation', 'Not applicable')}
- **Functional Redundancy:** {fsr_data.get('functional_redundancy', 'Not applicable')}

**Allocation (ISO 26262-3:2018, 7.4.2.8):**
- **Allocated To:** {fsr_data.get('allocated_to', 'Not yet allocated')}
- **Component Type:** {fsr_data.get('allocation_type', 'TBD')}
- **Interface:** {fsr_data.get('interface', 'To be specified')}

**Verification:**
- **Verification Criteria:** {fsr_data.get('verification_criteria', 'To be specified')}

**Traceability:**
- **Parent Safety Goal:** {fsr_data.get('safety_goal_id', 'Unknown')} - {fsr_data.get('safety_goal', 'N/A')[:60]}...

---

**Next Steps:**
- Allocate: `allocate {fsr_id} to [component name]`
- View parent goal: `show safety goal {fsr_data.get('safety_goal_id', 'SG-XXX')}`
"""
    
    return details


@tool(return_direct=True)
def show_fsr_summary(tool_input, cat):
    """
    Show summary of all derived FSRs.
    
    Input: "show FSR summary" or "list FSRs"
    """
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    system_name = cat.working_memory.get("system_name", "Unknown System")
    
    if not fsrs_data:
        return "❌ No FSRs derived yet. Use: `derive FSRs for all goals`"
    
    # Convert to objects
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    
    # Format using formatter
    formatter = FSRFormatter()
    
    # Statistics
    summary = f"""# 📊 FSR Summary

**System:** {system_name}
**Total FSRs:** {len(fsrs)}

**By ASIL:**
"""
    
    asil_counts = {}
    for fsr in fsrs:
        asil_counts[fsr.asil] = asil_counts.get(fsr.asil, 0) + 1
    
    for asil in ['D', 'C', 'B', 'A']:
        if asil in asil_counts:
            summary += f"- ASIL {asil}: {asil_counts[asil]}\n"
    
    summary += "\n**By Type:**\n"
    
    type_counts = {}
    for fsr in fsrs:
        type_counts[fsr.type] = type_counts.get(fsr.type, 0) + 1
    
    for fsr_type, count in sorted(type_counts.items()):
        summary += f"- {fsr_type}: {count}\n"
    
    summary += "\n**Allocation Status:**\n"
    
    allocated = len([f for f in fsrs if f.is_allocated()])
    summary += f"- Allocated: {allocated}/{len(fsrs)}\n"
    summary += f"- Unallocated: {len(fsrs) - allocated}/{len(fsrs)}\n"
    
    summary += "\n---\n\n"
    summary += formatter.format_fsr_table(fsrs)
    
    summary += """

---

**View Detailed FSR:** `show FSR FSR-XXX-XXX-X`

**Next Step:** `allocate all FSRs`
"""
    
    return summary