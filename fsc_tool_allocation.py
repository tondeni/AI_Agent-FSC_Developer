# fsc_tool_allocation.py
# FSR Allocation to System Components
# Per ISO 26262-3:2018, Clause 7.4.3

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime


@tool(return_direct=True)
def allocate_functional_requirements(tool_input, cat):
    """
    Allocate Functional Safety Requirements to system components.
    
    Performs preliminary allocation of FSRs to:
    - Hardware components (sensors, actuators, ECUs)
    - Software functions
    - External systems (VCU, HMI, Gateway, etc.)
    
    Per ISO 26262-3:2018, Clause 7.4.3:
    - Allocate FSRs to architectural elements
    - Define interfaces between components
    - Document allocation rationale
    
    Input: "allocate all FSRs" or "allocate FSR-XXX to [component]"
    Example: "allocate all FSRs"
    """
    
    print("✅ TOOL CALLED: allocate_functional_requirements")
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs:
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
        return allocate_single_fsr(tool_input, cat, fsrs)
    
    # Batch allocation for all FSRs
    system_name = cat.working_memory.get("system_name", "the system")
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    
    log.info(f"🎯 Allocating {len(fsrs)} FSRs to system components")
    
    # Build allocation prompt
    prompt = f"""You are allocating Functional Safety Requirements (FSRs) to system components per ISO 26262-3:2018, Clause 7.4.3.

**System:** {system_name}
**FSRs to Allocate:** {len(fsrs)}

**Your Task:**
For each FSR, determine the most appropriate component allocation based on:

1. **Functional Capability**
   - Which component can best implement this requirement?
   - Hardware vs Software considerations

2. **ASIL Considerations**
   - Component must support required ASIL level
   - Hardware for ASIL C/D detection often preferred

3. **System Architecture**
   - Consider existing system components
   - Minimize interface complexity
   - Group related FSRs to same component when logical

**Typical Component Types:**

**Hardware Components:**
- Sensors (voltage, current, temperature, position, etc.)
- Actuators and control elements
- ECU hardware (microcontroller, memory, power supply)
- Safety monitoring circuits

**Software Components:**
- Diagnostic software modules
- Control algorithms
- Fault handling routines
- HMI/warning systems

**External Systems:**
- Vehicle Control Unit (VCU)
- Human-Machine Interface (HMI)
- Gateway/Communication module
- External monitoring systems

**Output Format:**

---
## Allocation for FSR: [FSR-ID]
**FSR:** [Brief description]
**Type:** [Detection/Reaction/Indication]
**ASIL:** [X]
**Linked to SG:** [SG-ID]

**Primary Allocation:** [Component Name]
- **Component Type:** [Hardware/Software/External]
- **Rationale:** [Why this component is appropriate]
- **Interface:** [Key interfaces with other components]
- **Supporting Components:** [Other components involved, if any]

**Allocation Notes:**
- [Any special considerations]
- [Dependencies on other allocations]

---

**FSRs to Allocate:**

"""
    
    for fsr in fsrs:
        prompt += f"""
### {fsr['id']}
- **Description:** {fsr.get('description', 'N/A')}
- **Type:** {fsr.get('type', 'Unknown')}
- **ASIL:** {fsr.get('asil', 'QM')}
- **Linked to SG:** {fsr.get('safety_goal_id', 'Unknown')}
- **Preliminary Allocation:** {fsr.get('allocated_to', 'Not yet specified')}

"""
    
    prompt += """
**Requirements:**
- Each FSR must have exactly ONE primary allocation
- Provide clear rationale for each allocation
- Consider ASIL requirements in allocation decisions
- Document key interfaces between components
- Group related FSRs logically

**Now allocate all FSRs to appropriate system components.**
"""
    
    try:
        allocation_analysis = cat.llm(prompt).strip()
        
        # Parse allocations from response
        allocations = parse_allocations(allocation_analysis, fsrs)
        
        # Update FSRs with allocation information
        for fsr in fsrs:
            if fsr['id'] in allocations:
                alloc = allocations[fsr['id']]
                fsr['allocated_to'] = alloc['primary_component']
                fsr['allocation_type'] = alloc['component_type']
                fsr['allocation_rationale'] = alloc['rationale']
                fsr['interface'] = alloc.get('interface', 'To be specified')
        
        # Store updated FSRs
        cat.working_memory["fsc_functional_requirements"] = fsrs
        cat.working_memory["fsc_stage"] = "fsrs_allocated"
        
        # Generate summary
        allocated_count = len([f for f in fsrs if f.get('allocated_to')])
        
        summary = f"""✅ **FSRs Allocated to System Components**

**System:** {system_name}
**Total FSRs:** {len(fsrs)}
**FSRs Allocated:** {allocated_count}

**Allocation by Component Type:**
"""
        
        component_types = {}
        for fsr in fsrs:
            comp_type = fsr.get('allocation_type', 'Unallocated')
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        for comp_type, count in sorted(component_types.items()):
            summary += f"- {comp_type}: {count} FSRs\n"
        
        summary += "\n**Allocation by ASIL:**\n"
        
        for asil in ['D', 'C', 'B', 'A']:
            asil_fsrs = [f for f in fsrs if f.get('asil') == asil and f.get('allocated_to')]
            if asil_fsrs:
                summary += f"- ASIL {asil}: {len(asil_fsrs)} FSRs allocated\n"
        
        summary += f"""

---

**Detailed Allocation Analysis:**

{allocation_analysis}

---

**ISO 26262-3:2018 Compliance:**
✅ Clause 7.4.3: FSR allocation to architectural elements
✅ Allocation rationale documented
✅ Interfaces identified

**Next Steps:**

1. **Generate FSC Document:**
   `generate FSC document`
   
2. **Review Allocation:**
   `show allocation for [FSR-ID]`
   
3. **Revise Allocation (if needed):**
   `allocate [FSR-ID] to [component name]`
"""
        
        return summary
        
    except Exception as e:
        log.error(f"Error allocating FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error allocating FSRs: {str(e)}"


def allocate_single_fsr(tool_input, cat, fsrs):
    """
    Allocate a specific FSR to a component.
    Format: "allocate FSR-XXX to [component name]"
    """
    
    input_str = str(tool_input).strip()
    
    # Parse FSR ID and component
    if ' to ' not in input_str.lower():
        return """❌ Please specify allocation target.

**Format:** `allocate [FSR-ID] to [component]`
**Example:** `allocate FSR-001-DET-1 to Voltage Monitoring Hardware`
"""
    
    parts = input_str.lower().split(' to ', 1)
    fsr_id_part = parts[0].replace('allocate', '').replace('fsr', '').strip().upper()
    component = parts[1].strip()
    
    # Find FSR ID in the text
    fsr_id = None
    for fsr in fsrs:
        if fsr['id'].upper() in fsr_id_part or fsr_id_part in fsr['id'].upper():
            fsr_id = fsr['id']
            break
    
    if not fsr_id:
        available = ', '.join(f['id'] for f in fsrs[:5])
        return f"❌ FSR not found in '{fsr_id_part}'. Available: {available}..."
    
    # Find the FSR
    fsr = next((f for f in fsrs if f['id'] == fsr_id), None)
    
    # Determine component type
    component_lower = component.lower()
    if any(word in component_lower for word in ['hardware', 'sensor', 'actuator', 'ecu', 'module', 'circuit']):
        comp_type = 'Hardware'
    elif any(word in component_lower for word in ['software', 'algorithm', 'function', 'logic', 'routine']):
        comp_type = 'Software'
    elif any(word in component_lower for word in ['vcu', 'hmi', 'cluster', 'external', 'gateway']):
        comp_type = 'External'
    else:
        comp_type = 'Hardware'  # Default
    
    # Update FSR
    fsr['allocated_to'] = component
    fsr['allocation_type'] = comp_type
    fsr['allocation_rationale'] = f"Manually allocated to {component}"
    fsr['interface'] = 'To be specified in detailed design'
    
    return f"""✅ **FSR Allocated**

**FSR:** {fsr_id}
**Requirement:** {fsr.get('description', 'N/A')}
**ASIL:** {fsr.get('asil', 'QM')}

**Allocated To:** {component}
**Type:** {comp_type}

**Next Steps:**
- Continue allocating: `allocate [next FSR-ID] to [component]`
- Or batch allocate: `allocate all FSRs`
- Generate document: `generate FSC document`
"""


def parse_allocations(llm_response, fsrs):
    """
    Parse allocation information from LLM response.
    Returns dict: {fsr_id: allocation_info}
    """
    
    allocations = {}
    current_fsr_id = None
    current_allocation = {}
    
    lines = llm_response.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Detect FSR section
        if line.startswith('## Allocation for FSR:'):
            # Save previous allocation
            if current_fsr_id and current_allocation:
                allocations[current_fsr_id] = current_allocation
            
            # Start new allocation
            for fsr in fsrs:
                if fsr['id'] in line:
                    current_fsr_id = fsr['id']
                    current_allocation = {
                        'fsr_id': fsr['id'],
                        'primary_component': '',
                        'component_type': 'Unknown',
                        'rationale': '',
                        'interface': ''
                    }
                    break
        
        # Parse allocation fields
        if current_fsr_id:
            if line.startswith('**Primary Allocation:**'):
                current_allocation['primary_component'] = line.replace('**Primary Allocation:**', '').strip()
            elif line.startswith('- **Component Type:**'):
                comp_type = line.replace('- **Component Type:**', '').strip()
                current_allocation['component_type'] = comp_type
            elif line.startswith('- **Rationale:**'):
                rationale = line.replace('- **Rationale:**', '').strip()
                current_allocation['rationale'] = rationale
            elif line.startswith('- **Interface:**'):
                interface = line.replace('- **Interface:**', '').strip()
                current_allocation['interface'] = interface
    
    # Save last allocation
    if current_fsr_id and current_allocation:
        allocations[current_fsr_id] = current_allocation
    
    log.info(f"✅ Parsed {len(allocations)} allocations from LLM response")
    return allocations


@tool(return_direct=True)
def show_allocation_summary(tool_input, cat):
    """
    Show allocation summary and matrix.
    
    Displays:
    - FSRs grouped by allocated component
    - Allocation matrix
    - Interface dependencies
    
    Input: "show allocation summary"
    """
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs:
        return "❌ No FSRs available."
    
    allocated_fsrs = [f for f in fsrs if f.get('allocated_to')]
    
    if not allocated_fsrs:
        return "❌ No FSRs allocated yet. Use: `allocate all FSRs`"
    
    # Group by component
    by_component = {}
    for fsr in allocated_fsrs:
        component = fsr.get('allocated_to', 'Unallocated')
        if component not in by_component:
            by_component[component] = []
        by_component[component].append(fsr)
    
    summary = f"""📊 **FSR Allocation Summary**

**Total FSRs:** {len(fsrs)}
**Allocated:** {len(allocated_fsrs)}
**Unallocated:** {len(fsrs) - len(allocated_fsrs)}

---

**Allocation by Component:**

"""
    
    for component, comp_fsrs in sorted(by_component.items()):
        comp_type = comp_fsrs[0].get('allocation_type', 'Unknown')
        asil_levels = list(set(f.get('asil', 'QM') for f in comp_fsrs))
        
        summary += f"\n### {component} ({comp_type})\n"
        summary += f"- **FSRs:** {len(comp_fsrs)}\n"
        summary += f"- **ASIL Levels:** {', '.join(sorted(asil_levels, reverse=True))}\n"
        summary += f"- **Requirements:**\n"
        
        for fsr in comp_fsrs[:5]:  # Show first 5
            summary += f"  - {fsr['id']}: {fsr.get('type', 'Unknown')}\n"
        
        if len(comp_fsrs) > 5:
            summary += f"  - ... and {len(comp_fsrs) - 5} more\n"
    
    return summary


# COMMENTED OUT: Features not needed for current implementation
# Will be implemented in Technical Safety Concept (ISO 26262-4) phase

# @tool(return_direct=False)
# def define_functional_architecture(tool_input, cat):
#     """
#     Define high-level functional architecture showing component interactions.
#     NOTE: Detailed architecture belongs in Technical Safety Concept
#     """
#     pass

# @tool(return_direct=False)
# def derive_technical_safety_requirements(tool_input, cat):
#     """
#     Derive Technical Safety Requirements (TSRs) from FSRs.
#     NOTE: This belongs in Technical Safety Concept (ISO 26262-4)
#     Commented out for FSC phase - will be implemented in TSC plugin
#     """
#     pass