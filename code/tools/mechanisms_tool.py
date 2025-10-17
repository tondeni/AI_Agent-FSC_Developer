# tools/mechanism_tools.py
# Tools for identifying and managing safety mechanisms

from cat.mad_hatter.decorators import tool
from cat.log import log
import sys
import os

# Add parent directory to path
plugin_folder = os.path.dirname(os.path.dirname(__file__))
sys.path.append(plugin_folder)

from generators.mechanism_generator import MechanismGenerator, MechanismFormatter
from core.models import FunctionalSafetyRequirement, SafetyGoal, SafetyMechanism, MechanismFSRMapping


@tool(
    return_direct=True,
    examples=[
        "identify safety mechanisms",
        "identify mechanisms for all FSRs",
        "generate safety mechanisms",
        "identify safety mechanisms for FSR-SG01-DET-1"
    ]
)
def identify_safety_mechanisms(tool_input, cat):
    """
    Identify and describe safety mechanisms for FSRs.
    
    Per ISO 26262-4:2018, Clause 6.4.5.4:
    Safety mechanisms detect, control, or tolerate faults to maintain safe state.
    
    Mechanism categories:
    - Diagnostic mechanisms (BIST, checksums, plausibility checks)
    - Redundancy (dual sensors, voting, lockstep cores)
    - Safe state management (shutdown sequences, degraded modes)
    - Watchdogs and supervision
    - Communication protection (CRC, sequence counters)
    
    Input: "identify mechanisms" or "identify mechanisms for FSR-XXX"
    """
    
    log.info("✅ TOOL CALLED: identify_safety_mechanisms")
    
    # Get data from working memory
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
    if not fsrs_data:
        return """❌ No FSRs available.

**Required Steps per ISO 26262-4:2018:**
1. Load HARA: `load HARA for [item]`
2. Develop strategies: `develop safety strategy for all goals`
3. Derive FSRs: `derive FSRs for all goals`
4. Identify mechanisms: `identify safety mechanisms`
"""
    
    # Convert to objects
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    goals = [SafetyGoal(**g) for g in goals_data]
    system_name = cat.working_memory.get("system_name", "the system")
    
    # Parse input to determine scope
    input_str = str(tool_input).strip().lower()
    
    # Check if targeting specific FSR
    fsr_id_match = None
    for fsr in fsrs:
        if fsr.id.lower() in input_str:
            fsr_id_match = fsr.id
            break
    
    # Load catalog path
    catalog_path = os.path.join(plugin_folder, "templates", "safety_mechanisms_catalog.json")
    
    try:
        # Initialize generator
        generator = MechanismGenerator(cat.llm, catalog_path)
        
        if fsr_id_match:
            # Generate for single FSR
            fsr = next((f for f in fsrs if f.id == fsr_id_match), None)
            if not fsr:
                return f"❌ FSR '{fsr_id_match}' not found."
            
            goal = next((g for g in goals if g.id == fsr.safety_goal_id), None)
            if not goal:
                return f"❌ Safety goal for FSR '{fsr_id_match}' not found."
            
            log.info(f"🔍 Identifying mechanisms for {fsr_id_match}")
            mechanisms, mapping = generator.generate_mechanisms_for_fsr(fsr, goal, system_name)
            
            if not mechanisms:
                return f"❌ Failed to generate mechanisms for {fsr_id_match}. Please try again."
            
            # Store in working memory
            existing_mechanisms = cat.working_memory.get("fsc_safety_mechanisms", [])
            existing_mappings = cat.working_memory.get("fsc_mechanism_mappings", [])
            
            # Merge new mechanisms
            mech_dict = {m.id: m.to_dict() for m in mechanisms}
            existing_mech_dict = {m['id']: m for m in existing_mechanisms}
            existing_mech_dict.update(mech_dict)
            
            # Update mapping
            mapping_dict = {m['fsr_id']: m for m in existing_mappings}
            mapping_dict[mapping.fsr_id] = mapping.to_dict()
            
            cat.working_memory.fsc_safety_mechanisms = list(existing_mech_dict.values())
            cat.working_memory.fsc_mechanism_mappings = list(mapping_dict.values())
            
            # Format output
            formatter = MechanismFormatter()
            output = formatter.format_mechanisms_summary(mechanisms, [mapping], [fsr], system_name)
            
        else:
            # Generate for all FSRs
            log.info(f"🔍 Identifying mechanisms for {len(fsrs)} FSRs")
            mechanisms, mappings = generator.generate_mechanisms_for_fsrs(fsrs, goals, system_name)
            
            if not mechanisms:
                return "❌ Failed to generate mechanisms. Please try again."
            
            # Store in working memory
            cat.working_memory.fsc_safety_mechanisms = [m.to_dict() for m in mechanisms]
            cat.working_memory.fsc_mechanism_mappings = [m.to_dict() for m in mappings]
            cat.working_memory.fsc_stage = "mechanisms_identified"
            
            # Format output
            formatter = MechanismFormatter()
            output = formatter.format_mechanisms_summary(mechanisms, mappings, fsrs, system_name)
        
        log.info(f"✅ Mechanisms identified: {len(mechanisms)}")
        
        return output
        
    except Exception as e:
        log.error(f"Error identifying mechanisms: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error identifying mechanisms: {str(e)}\n\nPlease try again or check the logs."


@tool(return_direct=True)
def show_mechanism_details(tool_input, cat):
    """
    Show detailed information about a specific safety mechanism.
    
    Examples:
    - "show mechanism SM-FSR-001-001"
    - "show details for SM-FSR-001-001"
    """
    
    log.info("✅ TOOL CALLED: show_mechanism_details")
    
    mechanisms_data = cat.working_memory.get("fsc_safety_mechanisms", [])
    
    if not mechanisms_data:
        return """❌ No safety mechanisms available.

**Required:** Identify mechanisms first using: `identify safety mechanisms`
"""
    
    # Extract mechanism ID from input
    input_str = str(tool_input).strip().upper()
    mech_id = None
    
    for m in mechanisms_data:
        if m['id'].upper() in input_str:
            mech_id = m['id']
            break
    
    if not mech_id:
        return f"❌ Mechanism ID not found in input: {tool_input}"
    
    # Find mechanism
    mechanism = next((m for m in mechanisms_data if m['id'] == mech_id), None)
    
    if not mechanism:
        return f"❌ Mechanism '{mech_id}' not found."
    
    # Convert to object for better handling
    mech = SafetyMechanism.from_dict(mechanism)
    
    # Format detailed output
    output = f"""**Safety Mechanism Details**

**ID:** {mech.id}
**Name:** {mech.name}
**Category:** {mech.get_mechanism_category()}

---

**Description:**
{mech.description}

---

**Technical Characteristics:**

- **Mechanism Type:** {mech.mechanism_type}
- **ASIL Suitability:** {', '.join(mech.asil_suitability)}
- **Diagnostic Coverage:** {mech.diagnostic_coverage}

"""
    
    if mech.detection_capability:
        output += f"- **Detection Capability:** {mech.detection_capability}\n"
    
    if mech.reaction_time:
        output += f"- **Reaction Time:** {mech.reaction_time}\n"
    
    if mech.independence_level:
        output += f"- **Independence Level:** {mech.independence_level}\n"
    
    output += "\n---\n\n"
    
    if mech.implementation_notes:
        output += f"**Implementation Notes:**\n{mech.implementation_notes}\n\n"
    
    if mech.verification_method:
        output += f"**Verification Method:**\n{mech.verification_method}\n\n"
    
    # Show applicable FSRs
    if mech.applicable_fsrs:
        output += f"**Applicable FSRs:**\n"
        for fsr_id in mech.applicable_fsrs:
            output += f"- {fsr_id}\n"
    
    return output


@tool(return_direct=True)
def show_mechanism_summary(tool_input, cat):
    """
    Show summary of all identified safety mechanisms.
    
    Groups mechanisms by type and shows coverage statistics.
    
    Examples:
    - "show mechanism summary"
    - "show all mechanisms"
    - "mechanism overview"
    """
    
    log.info("✅ TOOL CALLED: show_mechanism_summary")
    
    mechanisms_data = cat.working_memory.get("fsc_safety_mechanisms", [])
    mappings_data = cat.working_memory.get("fsc_mechanism_mappings", [])
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not mechanisms_data:
        return """❌ No safety mechanisms identified yet.

**Required:** `identify safety mechanisms`
"""
    
    # Convert to objects
    mechanisms = [SafetyMechanism.from_dict(m) for m in mechanisms_data]
    
    # Build output
    output = f"""**Safety Mechanisms Summary**

**Total Mechanisms:** {len(mechanisms)}
**FSRs Covered:** {len(mappings_data)}/{len(fsrs_data)}

---

**Mechanisms by Category:**

"""
    
    # Group by type
    by_type = {}
    for m in mechanisms:
        cat_name = m.get_mechanism_category()
        if cat_name not in by_type:
            by_type[cat_name] = []
        by_type[cat_name].append(m)
    
    for category, mechs in sorted(by_type.items()):
        output += f"\n### {category} ({len(mechs)} mechanisms)\n\n"
        
        for m in mechs:
            output += f"- **{m.name}** (`{m.id}`)\n"
            output += f"  - ASIL: {', '.join(m.asil_suitability)}\n"
            output += f"  - Coverage: {m.diagnostic_coverage}\n"
            output += f"  - FSRs: {', '.join(m.applicable_fsrs)}\n"
    
    output += "\n---\n\n"
    
    # Coverage analysis
    covered_fsrs = len([m for m in mappings_data if m.get('mechanism_ids')])
    uncovered_fsrs = len(fsrs_data) - covered_fsrs
    
    if uncovered_fsrs > 0:
        output += f"⚠️ **{uncovered_fsrs} FSRs** still need safety mechanisms identified.\n"
    else:
        output += "✅ All FSRs have safety mechanisms identified.\n"
    
    return output


@tool(return_direct=True)
def show_mechanisms_for_fsr(tool_input, cat):
    """
    Show which safety mechanisms are assigned to a specific FSR.
    
    Examples:
    - "show mechanisms for FSR-SG01-DET-1"
    - "what mechanisms implement FSR-SG01-DET-1"
    """
    
    log.info("✅ TOOL CALLED: show_mechanisms_for_fsr")
    
    mechanisms_data = cat.working_memory.get("fsc_safety_mechanisms", [])
    mappings_data = cat.working_memory.get("fsc_mechanism_mappings", [])
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not mechanisms_data or not mappings_data:
        return """❌ No safety mechanisms identified yet.

**Required:** `identify safety mechanisms`
"""
    
    # Extract FSR ID from input
    input_str = str(tool_input).strip().upper()
    fsr_id = None
    
    for f in fsrs_data:
        if f['id'].upper() in input_str:
            fsr_id = f['id']
            break
    
    if not fsr_id:
        return f"❌ FSR ID not found in input: {tool_input}"
    
    # Find FSR
    fsr = next((f for f in fsrs_data if f['id'] == fsr_id), None)
    if not fsr:
        return f"❌ FSR '{fsr_id}' not found."
    
    # Find mapping
    mapping_data = next((m for m in mappings_data if m['fsr_id'] == fsr_id), None)
    if not mapping_data:
        return f"❌ No mechanisms assigned to {fsr_id} yet.\n\nUse: `identify mechanisms for {fsr_id}`"
    
    mapping = MechanismFSRMapping.from_dict(mapping_data)
    
    # Build output
    output = f"""**Safety Mechanisms for {fsr_id}**

**FSR Description:** {fsr.get('description', 'N/A')}
**ASIL:** {fsr.get('asil', 'N/A')}
**Type:** {fsr.get('type', 'N/A')}

---

**Assigned Mechanisms ({len(mapping.mechanism_ids)}):**

"""
    
    for mech_id in mapping.mechanism_ids:
        mech_data = next((m for m in mechanisms_data if m['id'] == mech_id), None)
        if not mech_data:
            continue
        
        mech = SafetyMechanism.from_dict(mech_data)
        
        output += f"\n### {mech.name} (`{mech.id}`)\n\n"
        output += f"**Type:** {mech.get_mechanism_category()}\n"
        output += f"**Description:** {mech.description}\n"
        output += f"**Coverage:** {mech.diagnostic_coverage}\n"
        output += f"**ASIL:** {', '.join(mech.asil_suitability)}\n"
        output += "\n"
    
    output += "---\n\n"
    
    if mapping.coverage_rationale:
        output += f"**Coverage Rationale:**\n{mapping.coverage_rationale}\n\n"
    
    if mapping.residual_risk:
        output += f"⚠️ **Residual Risk:**\n{mapping.residual_risk}\n"
    
    return output