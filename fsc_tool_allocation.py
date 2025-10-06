# fsc_tool_allocation.py
# Manages allocation of Functional Safety Requirements to architectural elements
# Per ISO 26262-4:2018, Clause 6.4.4

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime


@tool(return_direct=True)
def allocate_functional_requirements(tool_input, cat):
    """
    Allocate Functional Safety Requirements (FSRs) to architectural elements.
    
    Creates allocation matrix showing which components/modules implement each FSR.
    
    Allocation targets:
    - Hardware components (sensors, actuators, ECUs)
    - Software modules
    - Communication interfaces
    - External systems (VCU, cloud, etc.)
    
    Input: "allocate all FSRs" or "allocate FSR-XXX to [component]"
    Example: "allocate FSR-001-DET-1 to Voltage Monitoring Hardware"
    """
    
    print("✅ TOOL CALLED: allocate_functional_requirements")
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs:
        return """❌ No FSRs available for allocation.

**Please first:**
1. Load HARA: `load HARA for [item]`
2. Derive FSRs: `derive all FSRs`
3. Then allocate: `allocate FSRs`
"""
    
    system_name = cat.working_memory.get("system_name", "the system")
    input_str = str(tool_input).strip().lower()
    
    # Check if specific FSR allocation or batch allocation
    if input_str in ["all", "allocate all", "all fsrs", ""]:
        return allocate_all_fsrs_interactive(cat, fsrs, system_name)
    else:
        return allocate_single_fsr(tool_input, cat, fsrs)


def allocate_all_fsrs_interactive(cat, fsrs, system_name):
    """
    Perform intelligent batch allocation of all FSRs using LLM analysis.
    """
    
    log.info(f"📋 Allocating {len(fsrs)} FSRs to architectural elements")
    
    # Build comprehensive prompt for LLM
    prompt = f"""You are a System Architect allocating Functional Safety Requirements to architectural elements per ISO 26262-4:2018, Clause 6.4.4.

**Context:**
- System: {system_name}
- Total FSRs to allocate: {len(fsrs)}

**Your Task:**
For each FSR, determine the most appropriate allocation to hardware, software, or external components.

**Allocation Guidelines:**

1. **Hardware Allocation** - Choose for:
   - Direct sensing/measurement (voltage, current, temperature)
   - Physical actuation (contactors, relays)
   - Time-critical operations requiring dedicated hardware
   - High diagnostic coverage requirements (ASIL C/D)

2. **Software Allocation** - Choose for:
   - Complex algorithms and logic
   - Data processing and validation
   - Coordination between components
   - Reconfigurable functions

3. **External System Allocation** - Choose for:
   - Functions crossing item boundaries
   - Vehicle-level decisions (e.g., VCU, HMI)
   - Driver notifications
   - Cloud or backend services

4. **Mixed Allocation** - Use when:
   - Function requires both HW and SW (e.g., sensor + processing)
   - Specify primary and supporting allocations

**Allocation Considerations:**
- ASIL level (higher ASIL → prefer hardware or proven SW)
- Timing constraints (FTTI → hardware for fast response)
- Complexity (complex logic → software)
- Independence requirements (redundant channels → separate HW)
- Cost and feasibility

**Output Format:**

For EACH FSR, provide:

---
## Allocation for FSR: [FSR-ID]
**FSR Description:** [brief description]
**ASIL:** [X]
**Type:** [detection/reaction/indication]

**Primary Allocation:** [Component Name]
- **Component Type:** [Hardware/Software/External]
- **Rationale:** [Why this allocation is appropriate]
- **Interface:** [How it connects to other components]
- **Implementation Notes:** [Key technical considerations]

**Supporting Allocations:** [If applicable]
- [Component 2]: [Role]

---

**FSRs to Allocate:**

"""
    
    # Add FSR details to prompt
    for fsr in fsrs:
        prompt += f"""
### {fsr['id']}
- **Description:** {fsr['description']}
- **ASIL:** {fsr['asil']}
- **Type:** {fsr['type']}
- **Parent Goal:** {fsr.get('parent_safety_goal', 'Unknown')}

"""
    
    prompt += """
**Important:**
1. Be specific with component names (e.g., "Voltage Sensor Module" not just "Hardware")
2. Consider the entire system architecture
3. Ensure allocations support the required timing (FTTI)
4. Maintain independence for redundant channels
5. Document interface types (analog, SPI, CAN, Ethernet, etc.)

**Now provide allocations for ALL FSRs following the format above.**
"""
    
    try:
        allocation_analysis = cat.llm(prompt).strip()
        
        # Parse allocations from LLM response
        allocations = parse_allocations(allocation_analysis, fsrs)
        
        # Update FSRs with allocation information
        for fsr in fsrs:
            allocation = allocations.get(fsr['id'])
            if allocation:
                fsr['allocated_to'] = allocation['primary_component']
                fsr['allocation_type'] = allocation['component_type']
                fsr['allocation_rationale'] = allocation['rationale']
                fsr['interface'] = allocation['interface']
                fsr['supporting_allocations'] = allocation.get('supporting', [])
        
        # Store updated FSRs and allocation matrix
        cat.working_memory["fsc_functional_requirements"] = fsrs
        cat.working_memory["fsc_allocation_matrix"] = allocations
        cat.working_memory["fsc_stage"] = "fsrs_allocated"
        
        # Generate summary
        hw_count = len([f for f in fsrs if f.get('allocation_type') == 'Hardware'])
        sw_count = len([f for f in fsrs if f.get('allocation_type') == 'Software'])
        ext_count = len([f for f in fsrs if f.get('allocation_type') == 'External'])
        mixed_count = len([f for f in fsrs if f.get('supporting_allocations')])
        
        summary = f"""✅ **Functional Safety Requirements Allocated**

**Allocation Summary:**
- Total FSRs: {len(fsrs)}
- Hardware: {hw_count} FSRs
- Software: {sw_count} FSRs
- External Systems: {ext_count} FSRs
- Mixed (HW+SW): {mixed_count} FSRs

**Distribution by ASIL:**
"""
        
        for asil in ['D', 'C', 'B', 'A']:
            asil_fsrs = [f for f in fsrs if f['asil'] == asil]
            if asil_fsrs:
                summary += f"\n- ASIL {asil}: {len(asil_fsrs)} FSRs allocated"
        
        summary += f"""

---

**Detailed Allocations:**

{allocation_analysis}

---

**Allocation Matrix:**

| FSR ID | Requirement | ASIL | Allocated To | Type | Interface |
|--------|-------------|------|--------------|------|-----------|
"""
        
        for fsr in fsrs[:10]:  # Show first 10 in table
            allocated = fsr.get('allocated_to', 'TBD')
            alloc_type = fsr.get('allocation_type', 'Unknown')
            interface = fsr.get('interface', 'TBD')
            summary += f"| {fsr['id']} | {fsr['description'][:40]}... | {fsr['asil']} | {allocated} | {alloc_type} | {interface} |\n"
        
        if len(fsrs) > 10:
            summary += f"\n... and {len(fsrs) - 10} more FSRs\n"
        
        summary += """

---

**ISO 26262-4:2018 Compliance:**
✅ Clause 6.4.4: FSR allocation complete
✅ Architectural elements identified

**Next Steps:**

1. **Define Functional Architecture:**
   - `define functional architecture` - Describe component interactions
   
2. **Derive Technical Safety Requirements:**
   - `derive all TSRs` - Refine FSRs into implementation details
   
3. **Review Allocation:**
   - `show allocation for [FSR-ID]` - View specific allocation
   - `revise allocation for [FSR-ID]` - Modify if needed

4. **Identify Safety Mechanisms:**
   - `identify safety mechanisms` - Propose technical solutions
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
    if any(word in component_lower for word in ['hardware', 'sensor', 'actuator', 'ecu', 'module']):
        comp_type = 'Hardware'
    elif any(word in component_lower for word in ['software', 'algorithm', 'function', 'logic']):
        comp_type = 'Software'
    elif any(word in component_lower for word in ['vcu', 'hmi', 'cluster', 'external', 'cloud']):
        comp_type = 'External'
    else:
        comp_type = 'Hardware'  # Default
    
    # Update FSR
    fsr['allocated_to'] = component
    fsr['allocation_type'] = comp_type
    fsr['allocation_rationale'] = f"Manually allocated to {component}"
    fsr['interface'] = 'TBD - To be specified'
    
    return f"""✅ **FSR Allocated**

**FSR:** {fsr_id}
**Requirement:** {fsr['description']}
**ASIL:** {fsr['asil']}

**Allocated To:** {component}
**Type:** {comp_type}

**Next Steps:**
- Continue allocating: `allocate [next FSR-ID] to [component]`
- Or batch allocate: `allocate all FSRs`
- Define interfaces: `define interface for {fsr_id}`
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
                        'interface': '',
                        'supporting': []
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


@tool(return_direct=False)
def define_functional_architecture(tool_input, cat):
    """
    Define high-level functional architecture showing component interactions.
    
    Describes:
    - Safety function blocks
    - Data flows between blocks
    - Internal vs external interfaces
    - Timing and dependencies
    
    Input: Architecture description or "generate architecture"
    Example: "define functional architecture"
    """
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    system_name = cat.working_memory.get("system_name", "the system")
    
    if not fsrs:
        return "❌ No FSRs available. Please derive FSRs first."
    
    # Check if FSRs are allocated
    allocated_count = len([f for f in fsrs if f.get('allocated_to')])
    if allocated_count == 0:
        return "❌ FSRs not yet allocated. Please allocate FSRs first."
    
    # Build architecture definition prompt
    prompt = f"""You are defining the Functional Architecture for {system_name} per ISO 26262-4:2018, Clause 6.4.4.

**Context:**
- System: {system_name}
- FSRs allocated: {allocated_count}

**Allocated Components:**
"""
    
    # Extract unique components
    components = set()
    for fsr in fsrs:
        if fsr.get('allocated_to'):
            components.add(fsr['allocated_to'])
    
    for comp in sorted(components):
        prompt += f"- {comp}\n"
    
    prompt += """

**Your Task:**
Define the high-level functional architecture that shows:

1. **Architecture Overview**
   - Main functional blocks
   - Safety-critical paths
   - Redundancy strategy

2. **Component Descriptions**
   - Purpose of each component
   - Safety functions implemented
   - ASIL level of functions

3. **Data Flows**
   - Critical data paths
   - Timing constraints
   - Communication protocols

4. **Interface Definitions**
   - Internal interfaces (within item)
   - External interfaces (crossing boundaries)
   - Safety protocols

5. **Dependencies**
   - Component dependencies
   - Power dependencies
   - Timing dependencies

**Output Format:**

# Functional Architecture for [System]

## Architecture Overview
[High-level description with main blocks]

## Component Descriptions

### [Component 1]
- **Purpose:** [What it does]
- **Safety Functions:** [Which FSRs implemented]
- **ASIL:** [Highest ASIL function]
- **Key Interfaces:** [What it connects to]

### [Component 2]
...

## Data Flow Diagram
[Text-based description of critical data paths]

## Interface Specifications

### Internal Interfaces
- [Interface 1]: [Type, Protocol, Timing]
- [Interface 2]: ...

### External Interfaces
- [Interface 3]: [Crossing item boundary]
- [Interface 4]: ...

## Timing Architecture
- [Critical timing paths]
- [FTTI considerations]

## Independence Analysis
- [How independence is achieved for redundant channels]

**Now generate the functional architecture description.**
"""
    
    try:
        architecture_description = cat.llm(prompt).strip()
        
        # Store in working memory
        cat.working_memory["fsc_functional_architecture"] = architecture_description
        cat.working_memory["fsc_stage"] = "architecture_defined"
        
        result = f"""✅ **Functional Architecture Defined**

{architecture_description}

---

**ISO 26262-4:2018 Compliance:**
✅ Clause 6.4.4: Functional architecture documented

**Next Steps:**
- Derive Technical Safety Requirements: `derive all TSRs`
- Identify Safety Mechanisms: `identify safety mechanisms`
- Review architecture: Ask questions about specific components
"""
        
        return result
        
    except Exception as e:
        log.error(f"Error defining architecture: {e}")
        return f"❌ Error defining architecture: {str(e)}"


@tool(return_direct=False)
def show_allocation_details(tool_input, cat):
    """
    Show detailed allocation information for a specific FSR.
    
    Input: FSR ID
    Example: "show allocation for FSR-001-DET-1"
    """
    
    fsr_id = str(tool_input).replace('FSR', '').replace('for', '').strip().upper()
    if not fsr_id.startswith('FSR'):
        fsr_id = 'FSR-' + fsr_id
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    fsr = next((f for f in fsrs if f['id'] == fsr_id), None)
    
    if not fsr:
        return f"❌ FSR '{fsr_id}' not found."
    
    details = f"""### Allocation Details: {fsr['id']}

**FSR Description:**
{fsr['description']}

**ASIL:** {fsr['asil']}
**Type:** {fsr['type']}
**Parent Safety Goal:** {fsr.get('parent_safety_goal', 'Unknown')}

---

**Allocation:**
- **Primary Component:** {fsr.get('allocated_to', 'Not yet allocated')}
- **Component Type:** {fsr.get('allocation_type', 'Unknown')}
- **Interface:** {fsr.get('interface', 'Not specified')}

**Rationale:**
{fsr.get('allocation_rationale', 'Not documented')}

**Supporting Allocations:**
"""
    
    supporting = fsr.get('supporting_allocations', [])
    if supporting:
        for supp in supporting:
            details += f"- {supp}\n"
    else:
        details += "None\n"
    
    details += """

---

**Actions:**
- Revise allocation: `revise allocation for {fsr_id}`
- View architecture: `show functional architecture`
- Continue workflow: `derive TSRs for {fsr_id}`
"""
    
    return details