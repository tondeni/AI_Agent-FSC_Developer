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
        "propose safety mechanisms for FSRs",
        "suggest mechanisms"
    ]
)
def identify_safety_mechanisms(tool_input, cat):
    """
    Identify and propose safety mechanisms for FSRs.
    
    Per ISO 26262-4:2018, Clause 6.4.5.
    """
    
    log.info("🔧 TOOL CALLED: identify_safety_mechanisms")
    
    # Get data
    fsrs = cat.working_memory.get('fsc_functional_requirements', [])
    system_name = cat.working_memory.get('system_name', 'System')
    
    if not fsrs:
        return "Error: No FSRs found. Please derive FSRs first."
    
    try:
        # Import mechanism identifier
        from ..generators.mechanism_generator import MechanismGenerator
        
        # Generate mechanisms
        generator = MechanismGenerator(llm_function=cat.llm)
        mechanisms = generator.identify_mechanisms(fsrs, system_name)
        
        # Store in working memory
        cat.working_memory['fsc_safety_mechanisms'] = mechanisms
        cat.working_memory['fsc_stage'] = 'mechanisms_identified'
        cat.working_memory['needs_formatting'] = True
        cat.working_memory['last_operation'] = 'mechanism_identification'
        
        # ✅ SIMPLE PLAIN TEXT OUTPUT
        output = f"Successfully identified safety mechanisms for {system_name}.\n\n"
        output += f"Proposed {len(mechanisms)} safety mechanisms for {len(fsrs)} FSRs.\n"
        output += "Mechanisms follow ISO 26262-4:2018, Clause 6.4.5 guidance.\n\n"
        
        # List mechanisms in simple format
        for mech in mechanisms:
            output += f"{mech['id']} - {mech['name']}\n"
            output += f"  Type: {mech['type']}\n"
            output += f"  Description: {mech['description']}\n"
            output += f"  Coverage: {mech.get('coverage', 'TBD')}\n"
            output += f"  Applicable to: {', '.join(mech.get('fsr_ids', []))}\n"
            output += "\n"
        
        log.info(f"✅ Identified {len(mechanisms)} mechanisms")
        
        return output
        
    except Exception as e:
        log.error(f"Error identifying mechanisms: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"Error identifying mechanisms: {str(e)}"


# @tool(return_direct=True)
# def show_mechanism_details(tool_input, cat):
#     """DETAIL TOOL: Shows complete information for ONE SPECIFIC mechanism by ID.
    
#     Use when user requests details about A SINGLE SPECIFIC MECHANISM using its ID.
    
#     Trigger phrases: "show mechanism SM-XXX", "mechanism details for SM-YYY"
#     NOT for: listing mechanisms, creating mechanisms, or mechanism summaries
    
#     Displays: Full mechanism description, type, coverage, implementation notes
#     Prerequisites: Mechanisms must be identified first
#     Input: REQUIRED - Mechanism ID like "SM-FSR-001-001"
#     """
    
#     log.warning(f"----------------✅ TOOL CALLED: show_mechanism_details with input {tool_input} ----------------")
    
#     mechanisms_data = cat.working_memory.get("fsc_safety_mechanisms", [])
    
#     if not mechanisms_data:
#         return """❌ No safety mechanisms available.

# **Required:** Identify mechanisms first using: `identify safety mechanisms`
# """
    
#     # Extract mechanism ID from input
#     input_str = str(tool_input).strip().upper()
#     mech_id = None
    
#     for m in mechanisms_data:
#         if m['id'].upper() in input_str:
#             mech_id = m['id']
#             break
    
#     if not mech_id:
#         return f"❌ Mechanism ID not found in input: {tool_input}"
    
#     # Find mechanism
#     mechanism = next((m for m in mechanisms_data if m['id'] == mech_id), None)
    
#     if not mechanism:
#         return f"❌ Mechanism '{mech_id}' not found."
    
#     # Convert to object for better handling
#     mech = SafetyMechanism.from_dict(mechanism)
    
#     # Format detailed output
#     output = f"""**Safety Mechanism Details**

# **ID:** {mech.id}
# **Name:** {mech.name}
# **Category:** {mech.get_mechanism_category()}

# ---

# **Description:**
# {mech.description}

# ---

# **Technical Characteristics:**

# - **Mechanism Type:** {mech.mechanism_type}
# - **ASIL Suitability:** {', '.join(mech.asil_suitability)}
# - **Diagnostic Coverage:** {mech.diagnostic_coverage}

# """
    
#     if mech.detection_capability:
#         output += f"- **Detection Capability:** {mech.detection_capability}\n"
    
#     if mech.reaction_time:
#         output += f"- **Reaction Time:** {mech.reaction_time}\n"
    
#     if mech.independence_level:
#         output += f"- **Independence Level:** {mech.independence_level}\n"
    
#     output += "\n---\n\n"
    
#     if mech.implementation_notes:
#         output += f"**Implementation Notes:**\n{mech.implementation_notes}\n\n"
    
#     if mech.verification_method:
#         output += f"**Verification Method:**\n{mech.verification_method}\n\n"
    
#     # Show applicable FSRs
#     if mech.applicable_fsrs:
#         output += f"**Applicable FSRs:**\n"
#         for fsr_id in mech.applicable_fsrs:
#             output += f"- {fsr_id}\n"
    
#     return output


# @tool(return_direct=True)
# def show_mechanism_summary(tool_input, cat):
#     """OVERVIEW TOOL: Shows summary of ALL identified safety mechanisms.
    
#     Use when user wants an OVERVIEW/SUMMARY of ALL MECHANISMS.
#     Shows statistics grouped by mechanism type/category.
    
#     Trigger phrases: "show mechanism summary", "list all mechanisms", "mechanism overview"
#     NOT for: creating mechanisms, single mechanism details, or FSR-specific mechanisms
    
#     Displays: Total mechanisms, grouped by category, FSR coverage statistics
#     Prerequisites: Mechanisms must be identified first
#     Input: Not required
#     """
    
#     log.warning(f"----------------✅ TOOL CALLED: show_mechanism_summary with input {tool_input} ----------------")
    
#     mechanisms_data = cat.working_memory.get("fsc_safety_mechanisms", [])
#     mappings_data = cat.working_memory.get("fsc_mechanism_mappings", [])
#     fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
#     if not mechanisms_data:
#         return """❌ No safety mechanisms identified yet.

# **Required:** `identify safety mechanisms`
# """
    
#     # Convert to objects
#     mechanisms = [SafetyMechanism.from_dict(m) for m in mechanisms_data]
    
#     # Build output
#     output = f"""**Safety Mechanisms Summary**

# **Total Mechanisms:** {len(mechanisms)}
# **FSRs Covered:** {len(mappings_data)}/{len(fsrs_data)}

# ---

# **Mechanisms by Category:**

# """
    
#     # Group by type
#     by_type = {}
#     for m in mechanisms:
#         cat_name = m.get_mechanism_category()
#         if cat_name not in by_type:
#             by_type[cat_name] = []
#         by_type[cat_name].append(m)
    
#     for category, mechs in sorted(by_type.items()):
#         output += f"\n### {category} ({len(mechs)} mechanisms)\n\n"
        
#         for m in mechs:
#             output += f"- **{m.name}** (`{m.id}`)\n"
#             output += f"  - ASIL: {', '.join(m.asil_suitability)}\n"
#             output += f"  - Coverage: {m.diagnostic_coverage}\n"
#             output += f"  - FSRs: {', '.join(m.applicable_fsrs)}\n"
    
#     output += "\n---\n\n"
    
#     # Coverage analysis
#     covered_fsrs = len([m for m in mappings_data if m.get('mechanism_ids')])
#     uncovered_fsrs = len(fsrs_data) - covered_fsrs
    
#     if uncovered_fsrs > 0:
#         output += f"⚠️ **{uncovered_fsrs} FSRs** still need safety mechanisms identified.\n"
#     else:
#         output += "✅ All FSRs have safety mechanisms identified.\n"
    
#     return output


# @tool(return_direct=True)
# def show_mechanisms_for_fsr(tool_input, cat):
#     """
#     Show which safety mechanisms are assigned to a specific FSR.
    
#     Examples:
#     - "show mechanisms for FSR-SG01-DET-1"
#     - "what mechanisms implement FSR-SG01-DET-1"
#     """
    
#     log.info("✅ TOOL CALLED: show_mechanisms_for_fsr")
    
#     mechanisms_data = cat.working_memory.get("fsc_safety_mechanisms", [])
#     mappings_data = cat.working_memory.get("fsc_mechanism_mappings", [])
#     fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
#     if not mechanisms_data or not mappings_data:
#         return """❌ No safety mechanisms identified yet.

# **Required:** `identify safety mechanisms`
# """
    
#     # Extract FSR ID from input
#     input_str = str(tool_input).strip().upper()
#     fsr_id = None
    
#     for f in fsrs_data:
#         if f['id'].upper() in input_str:
#             fsr_id = f['id']
#             break
    
#     if not fsr_id:
#         return f"❌ FSR ID not found in input: {tool_input}"
    
#     # Find FSR
#     fsr = next((f for f in fsrs_data if f['id'] == fsr_id), None)
#     if not fsr:
#         return f"❌ FSR '{fsr_id}' not found."
    
#     # Find mapping
#     mapping_data = next((m for m in mappings_data if m['fsr_id'] == fsr_id), None)
#     if not mapping_data:
#         return f"❌ No mechanisms assigned to {fsr_id} yet.\n\nUse: `identify mechanisms for {fsr_id}`"
    
#     mapping = MechanismFSRMapping.from_dict(mapping_data)
    
#     # Build output
#     output = f"""**Safety Mechanisms for {fsr_id}**

# **FSR Description:** {fsr.get('description', 'N/A')}
# **ASIL:** {fsr.get('asil', 'N/A')}
# **Type:** {fsr.get('type', 'N/A')}

# ---

# **Assigned Mechanisms ({len(mapping.mechanism_ids)}):**

# """
    
#     for mech_id in mapping.mechanism_ids:
#         mech_data = next((m for m in mechanisms_data if m['id'] == mech_id), None)
#         if not mech_data:
#             continue
        
#         mech = SafetyMechanism.from_dict(mech_data)
        
#         output += f"\n### {mech.name} (`{mech.id}`)\n\n"
#         output += f"**Type:** {mech.get_mechanism_category()}\n"
#         output += f"**Description:** {mech.description}\n"
#         output += f"**Coverage:** {mech.diagnostic_coverage}\n"
#         output += f"**ASIL:** {', '.join(mech.asil_suitability)}\n"
#         output += "\n"
    
#     output += "---\n\n"
    
#     if mapping.coverage_rationale:
#         output += f"**Coverage Rationale:**\n{mapping.coverage_rationale}\n\n"
    
#     if mapping.residual_risk:
#         output += f"⚠️ **Residual Risk:**\n{mapping.residual_risk}\n"
    
#     return output