# fsc_tool_fsr_derivation.py
# Derives Functional Safety Requirements (FSRs) from Safety Goals
# Per ISO 26262-4:2018, Clause 6.4.2 and 6.4.3

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime


@tool(return_direct=True)
def derive_functional_safety_requirements(tool_input, cat):
    """
    Derive Functional Safety Requirements (FSRs) from safety goals.
    
    Uses "How to Achieve" decomposition:
    - Detection: How to detect the fault/hazard?
    - Reaction: How to achieve the safe state?
    - Indication: How to communicate the fault?
    
    Each FSR:
    - Inherits ASIL from parent safety goal
    - Has unique ID (FSR-XXX)
    - Is measurable and verifiable
    - Traces back to safety goal
    
    Input: Safety goal ID or "all" for all goals
    Example: "derive FSRs for SG-003" or "derive all FSRs"
    """
    
    print("✅ TOOL CALLED: derive_functional_safety_requirements")
    
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    
    if not safety_goals:
        return """❌ No safety goals loaded.

**Please first:**
1. Load HARA: `load HARA for [item name]`
2. Then derive FSRs: `derive all FSRs`
"""
    
    # Parse input
    input_str = str(tool_input).strip().lower()
    derive_all = input_str in ["all", "all goals", "derive all", ""]
    
    if derive_all:
        goals_to_process = safety_goals
        log.info(f"📋 Deriving FSRs for ALL {len(goals_to_process)} safety goals")
    else:
        # Extract goal ID
        goal_id = str(tool_input).strip().upper()
        goals_to_process = [g for g in safety_goals if g['id'] == goal_id]
        
        if not goals_to_process:
            return f"""❌ Safety goal '{goal_id}' not found.

**Available goals:** {', '.join(g['id'] for g in safety_goals[:5])}...

Use: `derive FSRs for [goal ID]` or `derive all FSRs`
"""
    
    # Build comprehensive prompt for LLM
    system_name = cat.working_memory.get("system_name", "the system")
    
    prompt = f"""You are a Functional Safety Engineer deriving Functional Safety Requirements (FSRs) per ISO 26262-4:2018.

**Your Task:**
Decompose each safety goal into specific, measurable Functional Safety Requirements using the "How to Achieve" method.

**Context:**
- Item: {system_name}
- Number of safety goals to process: {len(goals_to_process)}

**FSR Decomposition Strategy:**

For EACH safety goal, derive FSRs in THREE categories:

1. **DETECTION Requirements (FSR-XXX-DET-Y)**
   - How will we DETECT the fault or hazardous condition?
   - What sensors, diagnostics, or monitoring is needed?
   - What are the detection thresholds and timing?
   
2. **REACTION Requirements (FSR-XXX-REACT-Y)**
   - How will we ACHIEVE the safe state?
   - What actions must be taken?
   - What is the timing constraint?
   
3. **INDICATION Requirements (FSR-XXX-IND-Y)**
   - How will we COMMUNICATE the fault?
   - Who/what needs to be notified (driver, VCU, other systems)?
   - What is the notification timing?

**FSR Quality Criteria (ISO 26262-4, Clause 6.4.3):**
✅ Measurable and verifiable
✅ Inherits ASIL from parent safety goal
✅ Specifies timing requirements where applicable
✅ Avoids implementation details (no "HOW to implement")
✅ Focuses on "WHAT needs to be achieved"

**Output Format for EACH Safety Goal:**

---
## FSRs for Safety Goal: [Goal ID] - [Goal Statement]
**Parent ASIL:** [X]

### Detection Requirements
- **FSR-[ID]-DET-1:** [Requirement statement] (ASIL [X])
  - *Rationale:* [Why this detection is needed]
  - *Verification:* [How to verify]
  
- **FSR-[ID]-DET-2:** [Requirement statement] (ASIL [X])
  - *Rationale:* [Why this detection is needed]
  - *Verification:* [How to verify]

### Reaction Requirements
- **FSR-[ID]-REACT-1:** [Requirement statement] (ASIL [X])
  - *Rationale:* [How this achieves safe state]
  - *Verification:* [How to verify]
  
- **FSR-[ID]-REACT-2:** [Requirement statement] (ASIL [X])
  - *Rationale:* [How this achieves safe state]
  - *Verification:* [How to verify]

### Indication Requirements
- **FSR-[ID]-IND-1:** [Requirement statement] (ASIL [X])
  - *Rationale:* [Why this indication is needed]
  - *Verification:* [How to verify]

---

**Safety Goals to Process:**

"""
    
    # Add each goal to the prompt
    for goal in goals_to_process:
        prompt += f"""
### Safety Goal: {goal['id']}
- **ASIL:** {goal['asil']}
- **Goal Statement:** {goal['goal']}
- **Safe State:** {goal.get('safe_state', 'Not specified - assume safe shutdown')}
- **FTTI:** {goal.get('ftti', 'Not specified - determine based on hazard severity')}
- **Hazard Context:** {goal.get('hazard', '')}
- **Operational Situation:** {goal.get('operational_situation', '')}

"""
    
    prompt += """
**Important Guidelines:**

1. **Number of FSRs:** Derive 2-5 FSRs per goal (based on complexity)
   - Simple goals: 2-3 FSRs
   - Complex goals: 4-5 FSRs

2. **ASIL Inheritance:** All FSRs inherit parent goal's ASIL unless:
   - Decomposition is explicitly applied (covered in separate step)
   - Indication requirements may be one level lower if justified

3. **Timing Requirements:**
   - Use FTTI as upper bound for reaction time
   - Detection should be faster than reaction
   - Indication can be slower but < 1 second typically

4. **Avoid Redundancy:** Don't duplicate similar requirements across categories

5. **Be Specific:** Use numbers, thresholds, and measurable criteria

**Now derive all FSRs following the format above.**
"""
    
    # Get LLM response
    try:
        fsr_derivation = cat.llm(prompt).strip()
        
        # Parse the FSRs from LLM response
        fsrs = parse_derived_fsrs(fsr_derivation, goals_to_process)
        
        # Store in working memory
        existing_fsrs = cat.working_memory.get("fsc_functional_requirements", [])
        
        # Merge new FSRs with existing (avoiding duplicates)
        for fsr in fsrs:
            if not any(existing['id'] == fsr['id'] for existing in existing_fsrs):
                existing_fsrs.append(fsr)
        
        cat.working_memory["fsc_functional_requirements"] = existing_fsrs
        cat.working_memory["fsc_stage"] = "fsrs_derived"
        
        # Generate summary
        summary = f"""✅ **Functional Safety Requirements Derived**

**Summary:**
- Safety Goals Processed: {len(goals_to_process)}
- Total FSRs Derived: {len(fsrs)}
- Detection FSRs: {len([f for f in fsrs if '-DET-' in f['id']])}
- Reaction FSRs: {len([f for f in fsrs if '-REACT-' in f['id']])}
- Indication FSRs: {len([f for f in fsrs if '-IND-' in f['id']])}

**ASIL Distribution:**
- ASIL D: {len([f for f in fsrs if f['asil'] == 'D'])} FSRs
- ASIL C: {len([f for f in fsrs if f['asil'] == 'C'])} FSRs
- ASIL B: {len([f for f in fsrs if f['asil'] == 'B'])} FSRs
- ASIL A: {len([f for f in fsrs if f['asil'] == 'A'])} FSRs

---

**Detailed FSRs:**

{fsr_derivation}

---

**ISO 26262-4:2018 Compliance:**
✅ Clause 6.4.2: FSR derivation complete
✅ Clause 6.4.3: FSRs specified and traceable

**Next Steps:**

1. **Allocate FSRs to Architecture:**
   - `allocate FSRs` - Assign FSRs to components

2. **Analyze Specific FSR:**
   - `show FSR [FSR-ID]` - View details
   
3. **Refine FSRs (if needed):**
   - `refine FSR [FSR-ID]` - Improve specific requirement

4. **Check ASIL Decomposition:**
   - `analyze decomposition opportunities` - Identify complex FSRs

**Quality Check:**
- [ ] All FSRs are measurable and verifiable
- [ ] Timing requirements specified where needed
- [ ] Traceability to parent safety goals maintained
- [ ] No implementation details in FSR statements
"""
        
        return summary
        
    except Exception as e:
        log.error(f"Error deriving FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error deriving FSRs: {str(e)}"


def parse_derived_fsrs(llm_response, safety_goals):
    """
    Parse FSRs from LLM response and structure them.
    Returns list of FSR dictionaries.
    """
    
    fsrs = []
    current_parent_goal = None
    
    lines = llm_response.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Detect parent goal
        if line.startswith('## FSRs for Safety Goal:') or line.startswith('### Safety Goal:'):
            # Extract goal ID
            for goal in safety_goals:
                if goal['id'] in line:
                    current_parent_goal = goal
                    break
        
        # Detect FSR line (starts with - **FSR-...)
        if line.startswith('- **FSR-') or line.startswith('**FSR-'):
            try:
                # Extract FSR ID
                fsr_id_end = line.find(':**')
                if fsr_id_end == -1:
                    fsr_id_end = line.find('**:', line.find('FSR-'))
                
                fsr_id = line[line.find('FSR-'):fsr_id_end].strip('* ')
                
                # Extract requirement text
                req_start = fsr_id_end + 3
                req_text = line[req_start:].split('(ASIL')[0].strip()
                
                # Extract ASIL
                asil = 'B'  # Default
                if 'ASIL' in line:
                    asil_part = line.split('ASIL')[-1]
                    asil = asil_part.strip()[0]  # Get first character (A/B/C/D)
                
                # Determine type
                fsr_type = 'detection'
                if '-REACT-' in fsr_id:
                    fsr_type = 'reaction'
                elif '-IND-' in fsr_id:
                    fsr_type = 'indication'
                
                # Create FSR entry
                fsr = {
                    'id': fsr_id,
                    'description': req_text,
                    'asil': asil,
                    'type': fsr_type,
                    'parent_safety_goal': current_parent_goal['id'] if current_parent_goal else 'Unknown',
                    'status': 'derived',
                    'allocated_to': None,
                    'verification_method': 'TBD',
                    'rationale': '',
                    'created_date': datetime.now().isoformat()
                }
                
                fsrs.append(fsr)
                
            except Exception as e:
                log.warning(f"Could not parse FSR line: {line} - {e}")
                continue
    
    log.info(f"✅ Parsed {len(fsrs)} FSRs from LLM response")
    return fsrs


@tool(return_direct=False)
def show_fsr_details(tool_input, cat):
    """
    Display detailed information about a specific FSR.
    
    Input: FSR ID (e.g., "FSR-001-DET-1")
    Example: "show FSR FSR-001-DET-1"
    """
    
    fsr_id = str(tool_input).strip().upper()
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs:
        return "❌ No FSRs derived yet. Use 'derive all FSRs' first."
    
    # Find the FSR
    fsr = next((f for f in fsrs if f['id'] == fsr_id), None)
    
    if not fsr:
        available = ', '.join(f['id'] for f in fsrs[:5])
        return f"❌ FSR '{fsr_id}' not found. Available: {available}..."
    
    details = f"""### FSR Details: {fsr['id']}

**Type:** {fsr['type'].title()}
**ASIL:** {fsr['asil']}
**Status:** {fsr['status']}

**Requirement:**
{fsr['description']}

**Parent Safety Goal:** {fsr.get('parent_safety_goal', 'Unknown')}

**Allocated To:** {fsr.get('allocated_to') or 'Not yet allocated'}

**Verification Method:** {fsr.get('verification_method', 'TBD')}

**Rationale:**
{fsr.get('rationale', 'Not specified')}

---

**Actions Available:**
- `allocate {fsr_id} to [component]` - Assign to component
- `refine FSR {fsr_id}` - Improve requirement
- `derive TSRs for {fsr_id}` - Create technical requirements
- `show trace for {fsr_id}` - View traceability
"""
    
    return details


@tool(return_direct=False)
def refine_fsr(tool_input, cat):
    """
    Refine a specific FSR based on feedback or analysis.
    
    Input: FSR ID and refinement instructions
    Example: "refine FSR-001-DET-1: add timing constraint of 50ms"
    """
    
    input_str = str(tool_input).strip()
    
    # Parse FSR ID and instructions
    parts = input_str.split(':', 1)
    if len(parts) < 2:
        return """❌ Please provide FSR ID and refinement instructions.

**Format:** `refine FSR [FSR-ID]: [instructions]`
**Example:** `refine FSR-001-DET-1: add timing constraint of 50ms`
"""
    
    fsr_id = parts[0].replace('FSR ', '').strip().upper()
    refinement_instructions = parts[1].strip()
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    fsr = next((f for f in fsrs if f['id'] == fsr_id), None)
    
    if not fsr:
        return f"❌ FSR '{fsr_id}' not found."
    
    # Build refinement prompt
    prompt = f"""You are refining a Functional Safety Requirement per ISO 26262-4:2018.

**Current FSR:**
- **ID:** {fsr['id']}
- **Type:** {fsr['type']}
- **ASIL:** {fsr['asil']}
- **Requirement:** {fsr['description']}
- **Parent Safety Goal:** {fsr['parent_safety_goal']}

**Refinement Instructions:**
{refinement_instructions}

**Your Task:**
Revise the FSR to incorporate the refinement while maintaining:
1. Measurability and verifiability
2. ASIL-appropriate rigor
3. Traceability to parent safety goal
4. No implementation details (focus on WHAT, not HOW)

**Output Format:**
Provide the refined FSR statement (just the requirement text, no preamble).
"""
    
    try:
        refined_text = cat.llm(prompt).strip()
        
        # Update FSR
        fsr['description'] = refined_text
        fsr['status'] = 'refined'
        fsr['last_modified'] = datetime.now().isoformat()
        
        return f"""✅ **FSR Refined Successfully**

**FSR ID:** {fsr_id}

**Updated Requirement:**
{refined_text}

**Next Steps:**
- Review refined FSR
- Continue with allocation or TSR derivation
- `show FSR {fsr_id}` to see full details
"""
        
    except Exception as e:
        log.error(f"Error refining FSR: {e}")
        return f"❌ Error refining FSR: {str(e)}"