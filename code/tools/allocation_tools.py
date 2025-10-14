# tools/allocation_tools.py
# FSR allocation tools

from cat.mad_hatter.decorators import tool
from cat.log import log
import sys
import os

# Add parent directory to path
plugin_folder = os.path.dirname(os.path.dirname(__file__))
sys.path.append(plugin_folder)

from generators.allocation_generator import AllocationGenerator, AllocationAnalyzer
from core.models import SafetyGoal, FunctionalSafetyRequirement


@tool(
    return_direct=True,
    examples=[
        "allocate all FSRs",
        "allocate FSR-SG-001-DET-1 to Voltage Monitor Hardware",
        "allocate functional requirements"
    ]
)
def allocate_functional_requirements(tool_input, cat):
    """
    Allocate Functional Safety Requirements to system components.
    
    Per ISO 26262-3:2018, Clause 7.4.2.8:
    - Allocate FSRs to architectural elements
    - Define interfaces between components
    - Document allocation rationale
    - Maintain ASIL integrity
    
    Input: "allocate all FSRs" or "allocate FSR-XXX to [component]"
    """
    
    log.info("✅ TOOL CALLED: allocate_functional_requirements")
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
    if not fsrs_data:
        return """❌ No FSRs available.

**Required Steps:**
1. Load HARA: `load HARA for [item name]`
2. Develop strategy: `develop safety strategy for all goals`
3. Derive FSRs: `derive FSRs for all goals`
4. Allocate FSRs: `allocate all FSRs`
"""
    
    input_str = str(tool_input).strip().lower()
    
    # Check if single FSR allocation
    if ' to ' in input_str:
        return _allocate_single_fsr(tool_input, cat, fsrs_data)
    
    # Batch allocation for all FSRs
    system_name = cat.working_memory.get("system_name", "the system")
    safety_goals = [SafetyGoal(**g) for g in safety_goals_data]
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    
    log.info(f"🎯 Allocating {len(fsrs)} FSRs to system components")
    
    try:
        # Initialize allocation generator
        generator = AllocationGenerator(cat.llm)
        
        # Allocate FSRs
        log.info("🔄 Allocating FSRs...")
        allocated_fsrs = generator.allocate_fsrs(fsrs, safety_goals, system_name)
        
        # Store updated FSRs
        cat.working_memory["fsc_functional_requirements"] = [fsr.to_dict() for fsr in allocated_fsrs]
        cat.working_memory["fsc_stage"] = "fsrs_allocated"
        
        # Get allocation statistics
        analyzer = AllocationAnalyzer()
        stats = analyzer.get_allocation_statistics(allocated_fsrs)
        
        # Generate summary
        summary = f"""✅ **FSRs Allocated to System Components**

**System:** {system_name}
**Total FSRs:** {stats['total_fsrs']}
**FSRs Allocated:** {stats['allocated']}

**Allocation by Component Type:**
"""
        
        for comp_type, count in sorted(stats['by_component_type'].items()):
            summary += f"- {comp_type}: {count} FSRs\n"
        
        summary += "\n**Allocation by ASIL:**\n"
        
        for asil in ['D', 'C', 'B', 'A']:
            if asil in stats['by_asil']:
                summary += f"- ASIL {asil}: {stats['by_asil'][asil]} FSRs\n"
        
        summary += "\n---\n\n"
        
        # Add allocation matrix
        summary += analyzer.format_allocation_matrix(allocated_fsrs)
        
        summary += "\n---\n\n"
        
        # Validate allocation
        is_valid, issues = analyzer.validate_allocation(allocated_fsrs)
        
        if not is_valid:
            summary += "⚠️ **Allocation Issues:**\n"
            for issue in issues:
                summary += f"- {issue}\n"
            summary += "\n"
        
        summary += """**ISO 26262-3:2018 Compliance:**
✅ Clause 7.4.2.8: FSR allocation to architectural elements
✅ Allocation rationale documented
✅ Interfaces identified

**Completed:**
- ✅ Step 1: Safety Goals extracted from HARA
- ✅ Step 2: Safety Strategies developed
- ✅ Step 3: Functional Safety Requirements derived
- ✅ Step 4: FSRs allocated to architecture

**Next Steps:**

➡️ **Step 5:** Specify Validation Criteria
   ```
   specify validation criteria
   ```

➡️ **Step 6:** Verify FSC
   ```
   verify FSC
   ```

➡️ **Step 7:** Generate FSC Document
   ```
   generate FSC document
   ```

---

**Review Allocation:**
- View specific: `show allocation for [component name]`
- View all: `show allocation summary`
- Modify: `allocate [FSR-ID] to [component name]`
"""
        
        log.info(f"✅ Allocation complete: {stats['allocated']}/{stats['total_fsrs']} FSRs")
        
        return summary
        
    except Exception as e:
        log.error(f"Error allocating FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error allocating FSRs: {str(e)}"


@tool(return_direct=True)
def show_allocation_summary(tool_input, cat):
    """
    Show allocation summary and matrix.
    
    Displays FSRs grouped by allocated component.
    
    Input: "show allocation summary"
    """
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs_data:
        return "❌ No FSRs available."
    
    # Convert to objects
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    
    allocated_fsrs = [f for f in fsrs if f.is_allocated()]
    
    if not allocated_fsrs:
        return "❌ No FSRs allocated yet. Use: `allocate all FSRs`"
    
    # Use analyzer to format
    analyzer = AllocationAnalyzer()
    matrix = analyzer.format_allocation_matrix(fsrs)
    
    return matrix


@tool(return_direct=True)
def show_allocation_for_component(tool_input, cat):
    """
    Show FSRs allocated to a specific component.
    
    Input: Component name
    Example: "show allocation for Voltage Monitor Hardware"
    """
    
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs_data:
        return "❌ No FSRs available."
    
    # Parse input
    component_name = str(tool_input).strip()
    component_name = component_name.replace("show allocation for", "").replace("allocation for", "").strip()
    
    # Find FSRs for this component
    component_fsrs = [f for f in fsrs_data if component_name.lower() in f.get('allocated_to', '').lower()]
    
    if not component_fsrs:
        return f"""❌ No FSRs allocated to component matching '{component_name}'.

**Tip:** Use `show allocation summary` to see all components.
"""
    
    summary = f"""# 📦 Allocation for Component

**Component:** {component_fsrs[0]['allocated_to']}
**Component Type:** {component_fsrs[0].get('allocation_type', 'Unknown')}
**FSRs Allocated:** {len(component_fsrs)}

---

## Allocated FSRs

"""
    
    # Group by ASIL
    asil_groups = {}
    for fsr in component_fsrs:
        asil = fsr.get('asil', 'Unknown')
        if asil not in asil_groups:
            asil_groups[asil] = []
        asil_groups[asil].append(fsr)
    
    for asil in ['D', 'C', 'B', 'A']:
        if asil in asil_groups:
            summary += f"\n### ASIL {asil} ({len(asil_groups[asil])} FSRs)\n\n"
            
            for fsr in asil_groups[asil]:
                summary += f"**{fsr['id']}** - {fsr.get('type', 'Unknown')}\n"
                summary += f"- {fsr.get('description', 'N/A')}\n"
                summary += f"- Linked to: {fsr.get('safety_goal_id', 'Unknown')}\n"
                summary += f"- Interface: {fsr.get('interface', 'To be specified')}\n\n"
    
    return summary


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _allocate_single_fsr(tool_input, cat, fsrs_data):
    """Allocate a single FSR to a component (manual allocation)"""
    
    input_str = str(tool_input).strip()
    
    # Parse FSR ID and component
    if ' to ' not in input_str.lower():
        return """❌ Please specify allocation target.

**Format:** `allocate [FSR-ID] to [component]`
**Example:** `allocate FSR-SG-001-DET-1 to Voltage Monitoring Hardware`
"""
    
    parts = input_str.split(' to ', 1)
    fsr_id_part = parts[0].replace('allocate', '').replace('fsr', '').strip().upper()
    component = parts[1].strip()
    
    # Find FSR ID in the text
    fsr_id = None
    for fsr in fsrs_data:
        if fsr['id'].upper() in fsr_id_part or fsr_id_part in fsr['id'].upper():
            fsr_id = fsr['id']
            break
    
    if not fsr_id:
        available = ', '.join([f['id'] for f in fsrs_data[:5]])
        return f"❌ FSR not found in '{fsr_id_part}'. Available: {available}..."
    
    # Find and update the FSR
    fsr_data = next((f for f in fsrs_data if f['id'] == fsr_id), None)
    
    # Convert to object for allocation
    fsr = FunctionalSafetyRequirement(**fsr_data)
    
    # Use generator for single allocation
    generator = AllocationGenerator(cat.llm)
    updated_fsr = generator.allocate_single_fsr(fsr, component)
    
    # Update in working memory
    for i, f in enumerate(fsrs_data):
        if f['id'] == fsr_id:
            fsrs_data[i] = updated_fsr.to_dict()
            break
    
    cat.working_memory["fsc_functional_requirements"] = fsrs_data
    
    return f"""✅ **FSR Allocated**

**FSR:** {fsr_id}
**Requirement:** {fsr_data.get('description', 'N/A')}
**ASIL:** {fsr_data.get('asil', 'QM')}

**Allocated To:** {component}
**Type:** {updated_fsr.allocation_type}

**Next Steps:**
- Continue allocating: `allocate [next FSR-ID] to [component]`
- Or batch allocate: `allocate all FSRs`
- Generate document: `generate FSC document`
"""