# fsc_tool_mechanisms.py
# Identifies Safety Mechanisms at Functional Level for FSC
# Per ISO 26262-3:2018, Clause 7.4.2.3 (fault detection, control, tolerance strategies)
# NOTE: Detailed TSR derivation belongs in Technical Safety Concept (ISO 26262-4, Clause 6)

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import json
import os


@tool(return_direct=False)
def note_preliminary_technical_considerations(tool_input, cat):
    """
    Document preliminary technical considerations for FSRs.
    
    This is NOT full TSR derivation (which belongs in ISO 26262-4 TSC).
    This documents initial thoughts on HW/SW realization to inform TSC phase.
    
    Input: "note technical considerations" or auto-generated during FSR allocation
    """
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs:
        return "No FSRs available yet."
    
    considerations = []
    
    for fsr in fsrs:
        if fsr.get('allocated_to'):
            alloc_type = fsr.get('allocation_type', 'Unknown')
            
            consideration = {
                'fsr_id': fsr['id'],
                'allocation': fsr['allocated_to'],
                'type': alloc_type,
                'note': f"Will require detailed TSR in TSC phase (ISO 26262-4)"
            }
            
            considerations.append(consideration)
    
    cat.working_memory["fsc_preliminary_technical_notes"] = considerations
    
    return f"Noted preliminary technical considerations for {len(considerations)} FSRs. Detailed TSRs will be developed in Technical Safety Concept phase."


@tool(return_direct=True)
def identify_safety_mechanisms(tool_input, cat):
    """
    Identify safety mechanisms at FUNCTIONAL level for FSRs.
    
    Per ISO 26262-3:2018, Clause 7.4.2.3, specify strategies for:
    - Fault detection and control
    - Transitioning to safe state
    - Fault tolerance
    - Driver warnings
    - Degradation strategies
    
    This is FUNCTIONAL-level mechanisms, not detailed implementation.
    Implementation details belong in Technical Safety Concept (ISO 26262-4).
    
    Input: "identify safety mechanisms" or "identify mechanisms for FSR-XXX"
    Example: "identify mechanisms for FSR-001-DET-1"
    """
    
    print("✅ TOOL CALLED: identify_safety_mechanisms")
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs:
        return "❌ No FSRs available. Please derive FSRs first."
    
    # Load safety mechanisms catalog (functional level)
    plugin_folder = os.path.dirname(__file__)
    catalog = load_safety_mechanisms_catalog(plugin_folder)
    
    if not catalog:
        return "❌ Safety mechanisms catalog not found."
    
    system_name = cat.working_memory.get("system_name", "the system")
    input_str = str(tool_input).strip().lower()
    
    # Determine scope
    if input_str in ["all", "identify all", "all mechanisms", ""]:
        fsrs_to_process = sorted(fsrs, key=lambda f: {'D': 4, 'C': 3, 'B': 2, 'A': 1}.get(f['asil'], 0), reverse=True)
        log.info(f"🛠️ Identifying functional-level mechanisms for {len(fsrs_to_process)} FSRs")
    else:
        fsr_id = str(tool_input).strip().upper()
        if not fsr_id.startswith('FSR-'):
            fsr_id = 'FSR-' + fsr_id
        fsrs_to_process = [f for f in fsrs if f['id'] == fsr_id]
        
        if not fsrs_to_process:
            return f"❌ FSR '{fsr_id}' not found."
    
    # Build mechanism identification prompt (FUNCTIONAL LEVEL)
    prompt = f"""You are identifying FUNCTIONAL-LEVEL Safety Mechanisms per ISO 26262-3:2018, Clause 7.4.2.3.

**IMPORTANT SCOPE:**
This is the Functional Safety Concept (FSC), NOT the Technical Safety Concept (TSC).
- FSC (ISO 26262-3): FUNCTIONAL strategies (what needs to be done)
- TSC (ISO 26262-4): TECHNICAL implementation (how to do it)

**Context:**
- System: {system_name}
- FSRs to process: {len(fsrs_to_process)}

**Your Task:**
For each FSR, identify FUNCTIONAL-LEVEL safety strategies per ISO 26262-3:2018, 7.4.2.3:

1. **Fault Detection Strategy** (7.4.2.3.b)
   - What type of detection is needed? (plausibility, range check, comparison, etc.)
   - NOT how to implement it technically

2. **Fault Control Strategy** (7.4.2.3.b)
   - How to control/react to detected faults?
   - What safe state to transition to?

3. **Fault Tolerance Strategy** (7.4.2.3.d)
   - Is redundancy needed?
   - What level of degraded functionality?

4. **Driver Warning Strategy** (7.4.2.3.f, g)
   - What warnings are needed?
   - Purpose: reduce exposure time or increase controllability?

5. **Timing Strategy** (7.4.2.3.h)
   - Fault Tolerant Time Interval (FTTI)
   - Fault Handling Time Interval

**Available Functional Mechanisms from Catalog:**

{format_functional_mechanisms_catalog(catalog)}

**Output Format:**

---
## Functional Safety Mechanisms for FSR: [FSR-ID]
**FSR:** [Brief description]
**ASIL:** [X]
**Type:** [detection/reaction/indication]

### Detection Strategy (7.4.2.3.b)
- **Functional Approach:** [What type of detection - e.g., "Plausibility check against physical limits"]
- **Rationale:** [Why this strategy addresses the hazard]

### Control/Reaction Strategy (7.4.2.3.c)
- **Safe State Transition:** [What safe state - e.g., "Disable function, maintain current state"]
- **Timing:** [FTTI consideration]

### Fault Tolerance Strategy (7.4.2.3.d)
- **Tolerance Approach:** [If applicable - e.g., "Redundant sensing with voting"]
- **Degradation:** [Reduced functionality, if applicable]

### Warning Strategy (7.4.2.3.f,g)
- **Driver Warning:** [If applicable - type and purpose]
- **Exposure/Controllability:** [Which is addressed]

### Notes for TSC Phase
- **Technical Realization:** [Brief note on HW vs SW realization]
- **TSC Input:** [What needs to be detailed in ISO 26262-4]

---

**FSRs to Process:**

"""
    
    for fsr in fsrs_to_process[:20]:
        prompt += f"""
### {fsr['id']}
- **Description:** {fsr['description']}
- **ASIL:** {fsr['asil']}
- **Type:** {fsr['type']}
- **Allocated To:** {fsr.get('allocated_to', 'Unknown')}

"""
    
    prompt += """
**Critical Reminders:**
1. Focus on FUNCTIONAL strategies (WHAT), not technical implementation (HOW)
2. Reference ISO 26262-3:2018, Clause 7.4.2.3 strategies
3. Note that detailed technical requirements will be in TSC (ISO 26262-4)
4. Keep descriptions at system/functional level

**Now identify functional safety mechanisms for all FSRs.**
"""
    
    try:
        mechanism_analysis = cat.llm(prompt).strip()
        
        # Parse mechanisms from response (functional level)
        mechanisms = parse_functional_mechanisms(mechanism_analysis, fsrs_to_process)
        
        # Store in working memory
        cat.working_memory["fsc_safety_mechanisms"] = mechanisms
        cat.working_memory["fsc_stage"] = "mechanisms_identified"
        
        # Update FSRs with mechanism links
        for fsr in fsrs:
            fsr_mechanisms = [m for m in mechanisms if m['fsr_id'] == fsr['id']]
            if fsr_mechanisms:
                fsr['safety_mechanisms'] = [m['mechanism_id'] for m in fsr_mechanisms]
        
        # Generate summary
        summary = f"""✅ **Functional Safety Mechanisms Identified (ISO 26262-3)**

**Summary:**
- FSRs Processed: {len(fsrs_to_process)}
- Total Functional Mechanisms: {len(mechanisms)}

**Mechanism Strategies by Type:**
"""
        
        strategy_types = {}
        for m in mechanisms:
            stype = m.get('strategy_type', 'Unknown')
            strategy_types[stype] = strategy_types.get(stype, 0) + 1
        
        for stype, count in sorted(strategy_types.items()):
            summary += f"- {stype}: {count}\n"
        
        summary += f"""

**ASIL Coverage:**
"""
        
        for asil in ['D', 'C', 'B', 'A']:
            asil_mechs = [m for m in mechanisms if m.get('asil') == asil]
            if asil_mechs:
                summary += f"- ASIL {asil}: {len(asil_mechs)} mechanisms\n"
        
        summary += f"""

---

**Detailed Functional Mechanism Analysis:**

{mechanism_analysis}

---

**ISO 26262-3:2018 Compliance:**
✅ Clause 7.4.2.3: Functional safety strategies specified
✅ Strategies for detection, control, tolerance, warnings

**IMPORTANT NOTE:**
These are FUNCTIONAL-LEVEL mechanisms as required by FSC (ISO 26262-3).
Detailed TECHNICAL implementation (TSRs) will be developed in the next phase:
→ Technical Safety Concept (ISO 26262-4, Clause 6)

**Next Steps:**

1. **Complete FSC:**
   - `analyze decomposition opportunities` - Check ASIL decomposition
   - `generate FSC document` - Create FSC work product

2. **After FSC Approval:**
   - Proceed to Technical Safety Concept (ISO 26262-4)
   - Derive detailed Technical Safety Requirements (TSRs)
   - Specify hardware/software implementation details

**Quality Check:**
- [ ] All ASIL C/D FSRs have functional mechanisms
- [ ] Strategies address detection, reaction, tolerance
- [ ] Timing requirements (FTTI) considered
- [ ] Driver warnings specified where needed
"""
        
        return summary
        
    except Exception as e:
        log.error(f"Error identifying mechanisms: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error identifying mechanisms: {str(e)}"


def load_safety_mechanisms_catalog(plugin_folder):
    """Load functional-level safety mechanisms catalog."""
    
    template_path = os.path.join(plugin_folder, "templates", "safety_mechanisms_catalog.json")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        log.error(f"Safety mechanisms catalog not found: {template_path}")
        return None
    except Exception as e:
        log.error(f"Error loading catalog: {e}")
        return None


def format_functional_mechanisms_catalog(catalog):
    """Format catalog for functional-level strategies."""
    
    formatted = ""
    
    # Focus on strategy types, not implementation details
    formatted += "\n### Detection Strategies\n"
    formatted += "- Plausibility checks (range, gradient, correlation)\n"
    formatted += "- Redundancy comparisons (dual sensors, voting)\n"
    formatted += "- Sequence monitoring (alive counters, timestamps)\n"
    formatted += "- Built-in diagnostics\n\n"
    
    formatted += "### Control/Reaction Strategies\n"
    formatted += "- Safe state transitions (shutdown, degraded mode)\n"
    formatted += "- Fault isolation (prevent propagation)\n"
    formatted += "- Limp-home mode\n\n"
    
    formatted += "### Fault Tolerance Strategies\n"
    formatted += "- Redundancy (dual/triple channels)\n"
    formatted += "- Graceful degradation\n"
    formatted += "- Fail-operational design\n\n"
    
    formatted += "### Warning Strategies\n"
    formatted += "- Driver warnings (visual, audible)\n"
    formatted += "- System notifications\n"
    formatted += "- Progressive warning levels\n"
    
    return formatted


def parse_functional_mechanisms(llm_response, fsrs):
    """Parse functional mechanisms from LLM response."""
    
    mechanisms = []
    current_fsr_id = None
    
    lines = llm_response.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Detect FSR section
        if line.startswith('## Functional Safety Mechanisms for FSR:'):
            for fsr in fsrs:
                if fsr['id'] in line:
                    current_fsr_id = fsr['id']
                    break
        
        # Extract strategy information
        if current_fsr_id:
            if line.startswith('### Detection Strategy'):
                strategy_type = 'Detection'
            elif line.startswith('### Control/Reaction Strategy'):
                strategy_type = 'Control/Reaction'
            elif line.startswith('### Fault Tolerance Strategy'):
                strategy_type = 'Fault Tolerance'
            elif line.startswith('### Warning Strategy'):
                strategy_type = 'Warning'
            
            if line.startswith('- **Functional Approach:**') or line.startswith('- **Safe State Transition:**'):
                mechanism_id = f"FSM-{current_fsr_id}-{len(mechanisms)+1:03d}"
                
                mechanisms.append({
                    'fsr_id': current_fsr_id,
                    'mechanism_id': mechanism_id,
                    'strategy_type': strategy_type if 'strategy_type' in locals() else 'General',
                    'asil': get_fsr_asil(current_fsr_id, fsrs),
                    'functional_description': line.split(':**')[1].strip() if ':**' in line else line,
                    'iso_clause': 'ISO 26262-3:2018, Clause 7.4.2.3'
                })
    
    log.info(f"✅ Parsed {len(mechanisms)} functional mechanisms")
    return mechanisms


def get_fsr_asil(fsr_id, fsrs):
    """Get ASIL level of FSR."""
    fsr = next((f for f in fsrs if f['id'] == fsr_id), None)
    return fsr['asil'] if fsr else 'B'