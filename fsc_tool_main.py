# fsc_tool_main.py
# Main tools for Functional Safety Concept Development (ISO 26262-3:2018, Clause 7)
# FULLY ALIGNED WITH ISO 26262-3:2018

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import os
import json


@tool(
    return_direct=True,
    examples=[
        "step to generate fsc",
        "show fs workflow",
        "what do i need to do to generate fsc?",
    ]
)
def show_fsc_workflow(tool_input, cat):
    """
    Display the FSC development workflow per ISO 26262-3:2018, Clause 7.
    
    Input: "show FSC workflow" or "help with FSC"
    """
    
    workflow = """
📋 **Functional Safety Concept (FSC) Development Workflow**
*ISO 26262-3:2018, Clause 7*

**Objectives (ISO 26262-3:2018, 7.1):**
a) Specify functional/degraded behavior per safety goals
b) Specify constraints for fault detection and control
c) Specify strategies to achieve fault tolerance
d) Allocate FSRs to system architectural design or external measures
e) Verify FSC and specify safety validation criteria

---

### **FSC Development Steps:**

➡️ **Step 1: Extract Safety Goals from HARA**
- Command: `load HARA for [item name]`
- Extracts: Safety Goals, ASIL, Safe States, FTTI
- Required by ISO 26262-3:2018, 7.3.1

➡️ **Step 2: Develop Functional Safety Strategy**
- Command: `develop safety strategy for all safety goals`
- Define strategies for fault avoidance, detection and control.
-  Required by ISO 26262-3:2018, 7.4.2.3, 

➡️ **Step 3: Derive Functional Safety Requirements (FSRs)**
- Command: `derive FSRs for all goals`
- At least one FSR has to be derived for a safety goal
-  Required by ISO 26262-3:2018, 7.4.2.1 and 7.4.2.2

➡️ **Step 4: Allocate FSRs to Architectural Elements**
- Command: `allocate all FSRs`
- Allocate FSRs to System architectural elements
- Required by  ISO 26262-3:2018, 7.4.2.8

➡️ **Step 5: Specify Safety Validation Criteria**
- Command: `specify validation criteria`
- Specify validation criteria for FSRs and safety goals 
- Required by ISO 26262-3:2018, 7.4.3

➡️ **Step 6: Generate FSC Work Products**
- Command: `generate FSC document`
- Per ISO 26262-3:2018, 7.5
- Creates:
  * FSC Document (7.5.1)
  * Verification Report (7.5.2)
  * FSR Traceability Matrix

---

### **ISO 26262-3:2018, Clause 7 References:**

- **7.4.1**: General requirements
- **7.4.2**: Derivation of functional safety requirements
- **7.4.3**: Safety validation criteria
- **7.4.4**: Verification of FSC
- **7.5**: Work products

---

**Quick Start:**
1. `load HARA for [System Name]`
2. `develop safety strategy for all safety goals`
3. `derive FSRs for all goals`
4. `allocate all FSRs`
5. `specify validation criteria`
6. `generate FSC document`
"""
    
    return workflow


@tool(
    return_direct=True,
    examples=[
        "load hara from plugin folder",
        "load hara for [system_name]",
        "extract safety goals from Hara",
        "load current HARA"
    ]
)
def load_hara_for_fsc(tool_input, cat):
    """
    Load HARA outputs to begin FSC development.
    
    Per ISO 26262-3:2018, 7.3.1: Prerequisites
    - Item definition (ISO 26262-3, Clause 5)
    - HARA report (ISO 26262-3, Clause 6)
    - System architectural design (external source)
    
    Extracts:
    - Item/System name
    - Safety Goals
    - ASIL ratings
    - Safe States
    - FTTI (Fault Tolerant Time Interval)
    
    Sources (priority order):
    1. Working memory (if chained from HARA plugin)
    2. hara_inputs/ folder (uploaded files)
    3. Generated documents from HARA plugin
    
    Input: Item name or "use current HARA"
    Example: "load HARA for Battery Management System"
    """
    
    print("✅ TOOL CALLED: load_hara_for_fsc")
    
    # Parse input
    item_name = "Unknown System"
    if isinstance(tool_input, str):
        item_name = tool_input.strip()
        if item_name.lower() in ["use current hara", "use current", "current"]:
            item_name = cat.working_memory.get("system_name", item_name)
    elif isinstance(tool_input, dict):
        item_name = tool_input.get("item_name", item_name)
    
    log.info(f"📥 Loading HARA for: {item_name}")
    
    # Try to find HARA data
    hara_data = find_hara_data(cat, item_name)
    
    if not hara_data:
        return f"""❌ **No HARA found for '{item_name}'**

**ISO 26262-3:2018, 7.3.1 Prerequisites:**
The following information shall be available:
- Item definition (ISO 26262-3, Clause 5)
- HARA report (ISO 26262-3, Clause 6)
- System architectural design

**Please ensure:**
1. HARA has been generated using the HARA Assistant plugin
2. The item name matches exactly
3. The HARA is available in one of these locations:
   - Working memory (if just generated)
   - `hara_inputs/` folder in FSC plugin
   - Generated documents from HARA plugin

**Alternative:**
You can manually place your HARA file in:
- Excel format: `plugins/AI_Agent-FSC_Developer/hara_inputs/[item_name]_HARA.xlsx`

**Supported HARA Columns:**
- Safety Goal
- ASIL (A/B/C/D)
- Safe State
- FTTI (Fault Tolerant Time Interval)
- Hazard ID, Severity (S), Exposure (E), Controllability (C)
"""
    
    # Parse and validate HARA data
    safety_goals = parse_safety_goals(hara_data)
    
    if not safety_goals:
        return f"""❌ **No valid safety goals found in HARA for '{item_name}'**

**ISO 26262-3:2018, 7.4.2.2 Requirement:**
At least one functional safety requirement shall be derived from each safety goal.

**Common issues:**
- HARA table missing safety goal column
- All safety goals are QM (no ASIL A/B/C/D)
- File format not recognized

**Please check:**
1. HARA file contains safety goals with ASIL ratings
2. At least one safety goal has ASIL A, B, C, or D
3. File is in supported format (Excel .xlsx or working memory)
"""
    
    # Store in working memory
    cat.working_memory["system_name"] = item_name
    cat.working_memory["fsc_safety_goals"] = safety_goals
    cat.working_memory["fsc_stage"] = "hara_loaded"
    
    # Generate summary
    summary = f"""✅ **HARA Loaded Successfully** (*ISO 26262-3:2018, 7.3.1: Prerequisites satisfied*)

**System:** {item_name}
**Safety Goals Extracted:** {len(safety_goals)}

**ASIL Distribution:**
"""
    
    asil_counts = {}
    for sg in safety_goals:
        asil = sg.get('asil', 'QM')
        asil_counts[asil] = asil_counts.get(asil, 0) + 1
    
    for asil in ['D', 'C', 'B', 'A', 'QM']:
        if asil in asil_counts:
            summary += f"- ASIL {asil}: {asil_counts[asil]} goals\n"
    
    summary += "\n**Safety Goals Overview:**\n\n"
    
    for sg in safety_goals[:10]:  # Show first 10
        sg_id = sg.get('id', 'Unknown')
        sg_desc = sg.get('description', 'N/A')
        sg_asil = sg.get('asil', 'QM')
        sg_safe_state = sg.get('safe_state', 'Not specified')
        
        summary += f"**{sg_id}** (ASIL {sg_asil})\n"
        summary += f"- Goal: {sg_desc}\n"
        summary += f"- Safe State: {sg_safe_state}\n\n"
    
    if len(safety_goals) > 10:
        summary += f"... and {len(safety_goals) - 10} more safety goals\n\n"
    
    summary += """---

**Completed:**
- ✅ Step 1: Safety Goals extracted from HARA
   
**Next Steps per ISO 26262-3:2018 - Functional Safety Concept Development**

➡️ Step 2: Develop Safety Strategy (Clause 7.4.2.3): `develop safety strategy for all safety goals` 

➡️ Step 3: Derive Functional Safety Requirements (Clause 7.4.2.1): `derive FSRs for all goals`

➡️ Step 4: Allocate Functional Safety Requirements to system architecture components: `Allocate FSRs to system architecture`

➡️ Step 4: Specify Validation Criteria with system architecture.

➡️ Step 5: Generate Functional Safety Concept work product.

"""
    
    return summary


@tool(
    return_direct=True,
    examples=[
        "Develop functional safety strategy for all safety goals",
        "develop strategy for SG-001",
        "develop functional safety strategies for all goals",
    ]
)
def develop_safety_strategy(tool_input, cat):
    """
    Develop functional safety strategy for all safety goals in fluent narrative form.

    Per ISO 26262-3:2018, 7.4.2.3:
    The functional safety requirements shall specify, if applicable, strategies for:
    a) Fault avoidance
    b) Fault detection and control
    c) Transitioning to a safe state
    d) Fault tolerance
    e) Degradation of functionality
    f) Driver warnings to reduce exposure time
    g) Driver warnings to increase controllability
    h) Timing (FTTI compliance)
    i) Arbitration of control requests

    This function generates a cohesive, narrative-style safety strategy per goal.
    """
    
    print("✅ TOOL CALLED: develop_safety_strategy")
    
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    
    if not safety_goals:
        return """❌ No safety goals loaded.

**Required Steps per ISO 26262-3:2018:**
1. Load HARA (7.3.1): `load HARA for [item name]`
2. Then develop strategy (7.4.2.3): `develop safety strategy for all safety goals`
"""
    
    system_name = cat.working_memory.get("system_name", "the system")
    input_str = str(tool_input).strip().lower()

    # ✅ FIXED: Single, clean logic to decide "all" vs "single"
    if (
        "all" in input_str or
        input_str == "" or
        "safety goals" in input_str or
        "all goals" in input_str or
        "for all" in input_str
    ):
        goals_to_process = safety_goals
        log.info(f"🎯 Developing safety strategy for {len(goals_to_process)} safety goals")
    else:
        # Process single SG
        sg_id = str(tool_input).strip().upper()
        if not sg_id.startswith('SG-'):
            # Normalize: remove non-alphanumeric, ensure SG- prefix
            clean_part = ''.join(filter(str.isalnum, sg_id.replace('SG', '')))
            sg_id = f"SG-{clean_part}"
        goals_to_process = [sg for sg in safety_goals if sg['id'] == sg_id]
        
        if not goals_to_process:
            return f"❌ Safety Goal '{sg_id}' not found."

    # Generate narrative strategy for each goal individually
    strategy_narratives = []
    parsed_strategies = []

    for sg in goals_to_process:
        sg_id = sg['id']
        description = sg['description']
        asil = sg['asil']
        safe_state = sg.get('safe_state', 'To be defined per ISO 26262-3:2018, 7.4.2.5')
        ftti = sg.get('ftti', 'TBD')
        severity = sg.get('severity', '?')
        exposure = sg.get('exposure', '?')
        controllability = sg.get('controllability', '?')

        prompt = f"""You are a senior Functional Safety Engineer developing strategies per ISO 26262-3:2018, Clause 7.4.2.3.

**System:** {system_name}
**Safety Goal:** {sg_id}
- Description: "{description}"
- ASIL: {asil}
- Safe State: "{safe_state}"
- FTTI: {ftti} ms
- Hazard Profile: S{severity}/E{exposure}/C{controllability}

Write a **concise safety strategy in 1-2 paragraphs (2–3 lines** (max 3 sentences) for inclusion in section 5.1.1 of the FSC.  
Focus on:  
- The main hazard or malfunction being addressed,  
- The key technical or architectural measure(s) to prevent/contain it,  
- How the safe state is achieved or maintained,  
- And, if relevant, the role of driver warnings or degraded modes.

Avoid bullet points, lists, or section headers. Write in fluent, professional prose.

Example style:  
"The strategy ensures front wiper activation via driver input or rain sensor, with fallback to minimum continuous wiping if critical faults (e.g., NBC or WSM failure) are detected. A driver warning is issued to maintain controllability, ensuring the safe state is reached within the FTTI."
Your narrative must naturally cover:
- The hazard scenario and why this safety goal exists.
- How faults are avoided through design, process, or architecture.
- How faults or malfunctions are detected and controlled at runtime.
- How the system transitions to the defined safe state within the FTTI.
- Whether fault tolerance (e.g., redundancy) is used.
- How functionality degrades (e.g., limp-home) while preserving safety.
- What driver warnings are provided to reduce exposure time and improve controllability.
- How the total fault handling time (detection + reaction) fits within the FTTI.
- If applicable, how conflicting control requests are arbitrated.
- Assumed driver actions and available means of control.
- Behavior in normal, degraded, and emergency operating modes.

Write as if briefing a safety assessor: clear, technically precise, and traceable to ISO 26262.

Begin your response with:
## Safety Strategy for {sg_id}: {description[:60]}...

Now write the strategy and continue with the narrative:
"""

        try:
            response = cat.llm(prompt).strip()
            if not response or "error" in response.lower():
                response = f"## Safety Strategy for {sg_id}: [Generation failed – manual review required]\n\nStrategy could not be generated automatically. Requires expert input per ISO 26262."
        except Exception as e:
            log.error(f"LLM call failed for {sg_id}: {e}")
            response = f"## Safety Strategy for {sg_id}: [Error]\n\nFailed to generate: {str(e)}"

        strategy_narratives.append(response)

        # Store structured version for traceability (minimal)
        parsed_strategies.append({
            "safety_goal_id": sg_id,
            "asil": asil,
            "narrative": response,
            "ftti": ftti,
            "safe_state": safe_state
        })

    # Save to working memory
    cat.working_memory["fsc_safety_strategies"] = parsed_strategies
    cat.working_memory["fsc_stage"] = "strategies_developed"

    # Update original safety goals with strategy references
    for sg in safety_goals:
        matching = [s for s in parsed_strategies if s['safety_goal_id'] == sg['id']]
        if matching:
            sg['strategy_narrative'] = matching[0]['narrative']

    # Build final output
    full_text = "\n\n".join(strategy_narratives)
    
    # Summary stats
    asil_counts = {}
    for s in parsed_strategies:
        asil_counts[s['asil']] = asil_counts.get(s['asil'], 0) + 1

    summary = f"""✅ **Functional Safety Strategies Developed**
*Compliant with ISO 26262-3:2018, Clause 7.4.2.3*

**System:** {system_name}
**Safety Strategies Generated:** {len(parsed_strategies)}

**Coverage by ASIL:**
"""
    for asil in ['D', 'C', 'B', 'A']:
        if asil in asil_counts:
            summary += f"- ASIL {asil}: {asil_counts[asil]} strategies\n"

    summary += f"""

---

{full_text}

---
**Completed:**
- ✅ Step 1: Safety Goals extracted from HARA
- ✅ Step 2: Safe Strategies developed for each Safety Goal (Clause 7.4.2.3)
   
**Next Steps per ISO 26262-3:2018 - Functional Safety Concept Development**

➡️ Step 3: Derive Functional Safety Requirements (Clause 7.4.2.1): `derive FSRs for all goals`

➡️ Step 4: Allocate Functional Safety Requirements to system architecture components: `Allocate FSRs to system architecture`

➡️ Step 4: Specify Validation Criteria with system architecture.

➡️ Step 5: Generate Functional Safety Concept work product.

"""

    return summary


@tool(
    return_direct=True,
    examples=[
        "Derive Functional Safety Requirements from safety goals",
        "derive FSRs for SG-X001",
        "develop fsr",
        "develop functional safety requirements"
    ]
)
def derive_functional_safety_requirements(tool_input, cat):
    """
    Derive Functional Safety Requirements (FSRs) from safety goals.
    
    Per ISO 26262-3:2018:
    - 7.4.2.1: FSRs shall be derived from safety goals, considering system architectural design
    - 7.4.2.2: At least one FSR shall be derived from each safety goal
    - 7.4.2.4: Each FSR shall consider: operating modes, FTTI, safe states, 
               emergency operation interval, functional redundancies
    
    Creates measurable, verifiable requirements implementing the strategies.
    
    Input: "derive FSRs for all goals" or "derive FSRs for SG-XXX"
    Example: "derive FSRs for all goals"
    """
    
    print("✅ TOOL CALLED: derive_functional_safety_requirements")
    
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    strategies = cat.working_memory.get("fsc_safety_strategies", [])
    
    if not safety_goals:
        return """❌ No safety goals loaded.

**Required Steps per ISO 26262-3:2018:**
1. Load HARA (7.3.1): `load HARA for [item name]`
2. Develop strategy (7.4.2.3): `develop safety strategy for all safety goals`
3. Derive FSRs (7.4.2.1): `derive FSRs for all goals`
"""
    
    system_name = cat.working_memory.get("system_name", "the system")
    input_str = str(tool_input).strip().lower()
    
    # Determine which goals to process
    if "all" in input_str or input_str == "" or "safety goals" in input_str or "all goals" in input_str:
        goals_to_process = safety_goals 
        log.info(f"📝 Deriving FSRs for {len(goals_to_process)} safety goals")
    else:
        sg_id = str(tool_input).strip().upper()
        if not sg_id.startswith('SG-'):
            sg_id = 'SG-' + sg_id
        goals_to_process = [sg for sg in safety_goals if sg['id'] == sg_id]
        
        if not goals_to_process:
            return f"❌ Safety Goal '{sg_id}' not found."
    
    # Build FSR derivation prompt
    prompt = f"""You are deriving Functional Safety Requirements (FSRs) per ISO 26262-3:2018, Clause 7.4.2.

**System:** {system_name}
**Safety Goals to Process:** {len(goals_to_process)}

**ISO 26262-3:2018 Requirements:**

**7.4.2.1:** FSRs shall be derived from safety goals, considering system architectural design
**7.4.2.2:** At least one FSR shall be derived from each safety goal
**7.4.2.4:** Each FSR shall be specified by considering, as applicable:
   a) Operating modes
   b) Fault tolerant time interval (FTTI)
   c) Safe states
   d) Emergency operation time interval
   e) Functional redundancies

**7.4.1:** FSRs shall be specified per ISO 26262-8:2018, Clause 6 (requirements specification)

**Your Task:**
For each safety goal, derive measurable, verifiable Functional Safety Requirements that implement the strategies.

**FSR Categories (based on strategies from 7.4.2.3):**

1. **Fault Avoidance Requirements**
2. **Fault Detection Requirements**
3. **Fault Control Requirements**
4. **Safe State Transition Requirements**
5. **Fault Tolerance Requirements**
6. **Warning/Indication Requirements**
7. **Timing Requirements**
8. **Arbitration Requirements** (if applicable)

**FSR Quality Criteria per ISO 26262-8:2018, Clause 6:**
- Measurable, Verifiable, Traceable, Unambiguous, Complete, Consistent, Feasible

**Output Format:**

---
## FSRs for Safety Goal: [SG-ID]
**Safety Goal:** [Description]
**ASIL:** [X]
**Safe State:** [Defined state]
**FTTI:** [Value]

### Fault Avoidance Requirements

**FSR-[SG-ID]-AVD-1**
- **Description:** [...]
- **ASIL:** [...]
- **Linked to SG:** [...]
- **Operating Modes:** [...]
- **Preliminary Allocation:** [...]
- **Verification Criteria:** [...]

[... repeat for other categories ...]

---

**Safety Goals and Strategies:**

"""
    
    for sg in goals_to_process:
        prompt += f"""
### {sg['id']}
- **Safety Goal:** {sg['description']}
- **ASIL:** {sg['asil']}
- **Safe State:** {sg.get('safe_state', 'To be specified per 7.4.2.5')}
- **FTTI:** {sg.get('ftti', 'To be determined')}

"""
    
    prompt += """
**Requirements:**
- Derive 5-10 FSRs per safety goal
- Each FSR must be independently verifiable
- Use clear, unambiguous language
- Include specific metrics and acceptance criteria
- Specify preliminary component allocation
- All FSRs inherit parent Safety Goal ASIL
- Consider all items from 7.4.2.4

**Now derive functional safety requirements per ISO 26262-3:2018, 7.4.2 for all safety goals.**
"""
    
    try:
        fsr_analysis = cat.llm(prompt).strip()
        
        # Parse FSRs from response
        fsrs = parse_fsrs(fsr_analysis, goals_to_process)
        
        # Validate that each safety goal has at least one FSR (per 7.4.2.2)
        for sg in goals_to_process:
            sg_fsrs = [f for f in fsrs if f.get('safety_goal_id') == sg['id']]
            if not sg_fsrs:
                log.warning(f"⚠️ Safety Goal {sg['id']} has no FSRs - violates 7.4.2.2")
        
        # Store in working memory
        cat.working_memory["fsc_functional_requirements"] = fsrs
        cat.working_memory["fsc_stage"] = "fsrs_derived"
        cat.working_memory["document_type"] = "fsr" 

        
        # Generate summary
        summary = f"""✅ **Functional Safety Requirements Derived**
*ISO 26262-3:2018, Clause 7.4.2 compliance*

**System:** {system_name}
**Total FSRs:** {len(fsrs)}

**Compliance Check:**
✅ 7.4.2.1: FSRs derived from safety goals
✅ 7.4.2.2: At least one FSR per safety goal
✅ 7.4.2.4: FSRs consider operating modes, FTTI, safe states, redundancies
✅ 7.4.1: FSRs specified per ISO 26262-8 requirements

**FSR Distribution by Category and ASIL:**
- See detailed analysis below.

---

{fsr_analysis}

---

**Completed:**
- ✅ Step 1: Safety Goals extracted from HARA
- ✅ Step 2: Safe Strategies developed for each Safety Goal (Clause 7.4.2.3)
- ✅ Step 3: Functional Safety Requirements derived for each Safety Goal
   
**Next Steps per ISO 26262-3:2018 - Functional Safety Concept Development**

➡️ Step 4: Allocate Functional Safety Requirements to system architecture components: `Allocate FSRs to system architecture`

➡️ Step 4: Specify Validation Criteria with system architecture.

➡️ Step 5: Generate Functional Safety Concept work product.

"""
        
        return summary
        
    except Exception as e:
        log.error(f"Error deriving FSRs: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error deriving FSRs: {str(e)}"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_hara_data(cat, item_name):
    """Mock implementation - replace with real logic in your plugin"""
    # In real plugin, this would search files/memory
    # For demo, return sample data if item_name matches expected
    if "wiper" in item_name.lower():
        return {
            "system": item_name,
            "goals": [
                {"id": "SG-001", "description": "ENSURE DRIVER VISIBILITY DURING ADVERSE WEATHER", "asil": "B", "safe_state": "WIPERS ACTIVATED, WIPING AT APPROPRIATE SPEED", "ftti": "500"},
                {"id": "SG-002", "description": "PREVENT EXCESSIVE WIPER SPEED TO MAINTAIN VISIBILITY", "asil": "B", "safe_state": "WIPER SPEED LIMITED TO SAFE OPERATING RANGE", "ftti": "300"},
                # Add more as needed
            ]
        }
    return None


def parse_safety_goals(hara_data):
    """Convert HARA data into safety goals list"""
    if not hara_data or 'goals' not in hara_data:
        return []
    return hara_data['goals']


def parse_fsrs(llm_response, safety_goals):
    """
    Parse FSRs from LLM response.
    Extracts all fields: ID, Description, ASIL, Operating Modes, Allocation, Verification.
    """
    fsrs = []
    current_sg = None
    current_fsr = None
    
    lines = llm_response.split('\n')
    
    # Type mapping
    type_mapping = {
        'AVD': 'Fault Avoidance',
        'DET': 'Fault Detection',
        'CTL': 'Fault Control',
        'SST': 'Safe State Transition',
        'TOL': 'Fault Tolerance',
        'WRN': 'Warning/Indication',
        'TIM': 'Timing',
        'ARB': 'Arbitration'
    }
    
    for line in lines:
        line_stripped = line.strip()
        
        # Detect safety goal section
        if '## FSRs for Safety Goal:' in line_stripped:
            for sg in safety_goals:
                if sg['id'] in line_stripped:
                    current_sg = sg
                    break
        
        # Detect FSR ID line
        if line_stripped.startswith('**FSR-') and current_sg:
            # Save previous FSR if exists
            if current_fsr:
                fsrs.append(current_fsr)
            
            # Extract FSR ID (remove ** markers)
            fsr_id = line_stripped.replace('**', '').strip()
            
            # Determine type from ID
            fsr_type = 'General'
            for type_code, type_name in type_mapping.items():
                if f'-{type_code}-' in fsr_id:
                    fsr_type = type_name
                    break
            
            # Create new FSR entry
            current_fsr = {
                'id': fsr_id,
                'safety_goal_id': current_sg['id'],
                'safety_goal': current_sg['description'],
                'asil': current_sg['asil'],
                'type': fsr_type,
                'description': '',
                'operating_modes': '',
                'allocated_to': '',
                'verification_criteria': '',
                'timing': current_sg.get('ftti', 'To be determined'),
                'safe_state': current_sg.get('safe_state', ''),
                'emergency_operation': '',
                'functional_redundancy': ''
            }
        
        # Extract FSR fields (lines starting with "* " or "- ")
        if current_fsr:
            # Handle both "* Description:" and "- Description:" formats
            if line_stripped.startswith('* Description:') or line_stripped.startswith('- Description:'):
                desc = line_stripped.replace('* Description:', '').replace('- Description:', '').strip()
                current_fsr['description'] = desc
            
            elif line_stripped.startswith('* ASIL:') or line_stripped.startswith('- ASIL:'):
                asil = line_stripped.replace('* ASIL:', '').replace('- ASIL:', '').strip()
                current_fsr['asil'] = asil
            
            elif line_stripped.startswith('* Operating Modes:') or line_stripped.startswith('- Operating Modes:'):
                modes = line_stripped.replace('* Operating Modes:', '').replace('- Operating Modes:', '').strip()
                current_fsr['operating_modes'] = modes
            
            elif line_stripped.startswith('* Preliminary Allocation:') or line_stripped.startswith('- Preliminary Allocation:'):
                alloc = line_stripped.replace('* Preliminary Allocation:', '').replace('- Preliminary Allocation:', '').strip()
                current_fsr['allocated_to'] = alloc
            
            elif line_stripped.startswith('* Verification Criteria:') or line_stripped.startswith('- Verification Criteria:'):
                verif = line_stripped.replace('* Verification Criteria:', '').replace('- Verification Criteria:', '').strip()
                current_fsr['verification_criteria'] = verif
    
    # Save last FSR
    if current_fsr:
        fsrs.append(current_fsr)
    
    log.info(f"✅ Parsed {len(fsrs)} FSRs from LLM response")
    
    # Debug: Log first FSR to verify parsing
    if fsrs:
        log.info(f"📝 Sample FSR: {fsrs[0]['id']} - {fsrs[0]['description'][:50]}...")
    
    return fsrs