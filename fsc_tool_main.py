# fsc_tool_main.py
# Main tool for Functional Safety Concept development
# Integrates with HARA outputs and guides FSC creation per ISO 26262-4:2018

import json
import os
from datetime import datetime
from cat.mad_hatter.decorators import tool
from cat.log import log

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    log.warning("openpyxl not available - Excel file reading will be disabled")


@tool(return_direct=True)
def show_fsc_workflow(tool_input, cat):
    """
    Display the complete FSC development workflow per ISO 26262-4:2018.
    
    Use this when user asks:
    - "How do I create an FSC?"
    - "FSC workflow"
    - "What are the FSC steps?"
    """
    
    workflow = """# 🛡️ Functional Safety Concept (FSC) Development Workflow

**ISO 26262-4:2018 Compliant Process**

---

## Prerequisites
✅ Item Definition completed (ISO 26262-3, Clause 5)
✅ HARA completed with safety goals (ISO 26262-3, Clause 6)

---

## FSC Development Steps

### **Step 1: Load HARA Outputs** 📥
**Command:** `load HARA for [Item Name]`

**What it does:**
- Imports safety goals from HARA
- Validates ASIL assignments
- Checks for completeness

**Output:**
- Summary of safety goals by ASIL
- Safe states and FTTIs extracted

---

### **Step 2: Refine Safety Goals (if needed)** ✏️
**Command:** `refine safety goal [SG-ID]` or `refine all safety goals`

**What it does:**
- Validates goal is result-oriented
- Ensures safe state is clearly defined
- Confirms FTTI is justified
- Adds measurable success criteria

**ISO Clause:** 6.4.6

---

### **Step 3: Derive Functional Safety Requirements (FSRs)** 🎯
**Command:** `derive FSRs for [SG-ID]` or `derive all FSRs`

**What it does:**
- Decomposes each safety goal into:
  - **Detection requirements** (How to detect faults?)
  - **Reaction requirements** (How to reach safe state?)
  - **Indication requirements** (How to inform driver/system?)
- Assigns unique FSR IDs
- Inherits ASIL from parent goal
- Establishes traceability

**ISO Clause:** 6.4.2, 6.4.3

**Example:**
```
Safety Goal SG-003: "Prevent unintended battery disconnect" (ASIL C)
↓
FSR-001: Detect contactor weld fault within 50ms (ASIL C)
FSR-002: Detect contactor open-circuit fault within 100ms (ASIL C)
FSR-003: Open redundant contactor within 200ms of fault detection (ASIL C)
FSR-004: Signal fault to VCU and driver within 500ms (ASIL B)
```

---

### **Step 4: Allocate FSRs to Architecture** 🏗️
**Command:** `allocate FSRs` or `allocate FSR-XXX to [component]`

**What it does:**
- Assigns FSRs to hardware/software/external elements
- Defines interfaces between components
- Documents allocation rationale
- Creates allocation matrix

**ISO Clause:** 6.4.4

**Allocation Matrix:**
| FSR ID | Requirement | Allocated To | Interface | Rationale |
|--------|-------------|--------------|-----------|-----------|
| FSR-001 | Detect weld | Contactor Monitor HW | Analog signal | Direct sensing |
| FSR-002 | Detect open | Software diagnostic | SPI bus | Software plausibility |

---

### **Step 5: Identify Functional Safety Mechanisms** 🛠️
**Command:** `identify safety mechanisms` or `identify mechanisms for [FSR-ID]`

**What it does:**
- Identifies FUNCTIONAL-level safety strategies
- Detection strategies (plausibility, redundancy)
- Reaction strategies (safe states, degradation)
- Fault tolerance strategies
- Warning strategies

**ISO Clause:** 7.4.2.3 (ISO 26262-3:2018)

**Important:** These are FUNCTIONAL strategies (WHAT to do), not technical implementation details (HOW to do it).

**Example:**
```
FSR-001: Detect contactor weld fault within 50ms
↓
Functional Mechanism:
- Detection Strategy: Redundant voltage sensing with comparison
- Control Strategy: Immediate transition to safe state (contactors open)
- Tolerance Strategy: Dual independent contactor paths
- Warning Strategy: Progressive driver warning (visual + audible)

NOTE: Detailed technical implementation (ADC specs, algorithms) 
      will be specified in TSC phase (ISO 26262-4)
```

---

### **Step 6: Analyze ASIL Decomposition (Optional)** 🧩
**Command:** `analyze decomposition for [FSR-ID]`

**What it does:**
- Evaluates if decomposition reduces complexity
- Checks independence requirements
- Calculates decomposed ASILs
- Documents justification

**Valid Decompositions:**
- ASIL D → ASIL B(D) + ASIL B(D)
- ASIL C → ASIL B(D) + ASIL A(D)
- ASIL B → ASIL A(D) + ASIL A(D)

**ISO Reference:** Part 9, Clause 5

---

### **Step 8: Define Verification Strategy** ✅
**Command:** `define verification strategy`

**What it does:**
- Specifies verification methods for each requirement
- Sets test coverage targets (per ASIL)
- Plans verification activities

**Methods:**
- Requirements review
- Design review
- Unit testing
- Integration testing
- Hardware-in-the-loop (HIL)
- System validation

---

### **Step 9: Verify Traceability** 🔗
**Command:** `verify traceability` or `show trace for [ID]`

**What it does:**
- Checks all safety goals have FSRs
- Verifies all FSRs are allocated
- Confirms mechanisms cover requirements
- Identifies orphaned items

**Traceability Chain:**
```
Safety Goal (SG-003)
  ├─> FSR-001 → TSR-001, TSR-002 → SM-DIAG-001
  ├─> FSR-002 → TSR-003 → SM-DIAG-002
  └─> FSR-003 → TSR-004, TSR-005 → SM-SAFE-001
```

---

### **Step 10: Generate FSC Document** 📄
**Command:** `generate FSC document`

**What it does:**
- Creates complete FSC work product (Word + Excel)
- Includes all sections per ISO 26262-4, Clause 7.5
- Generates traceability matrix
- Formats for review and approval

**Output Files:**
- `[System]_FSC_[Date].docx` - Complete FSC
- `[System]_FSC_Traceability_[Date].xlsx` - Trace matrix

**ISO Clause:** 7.5 (Work Products)

---

## Quick Commands

| Command | Description |
|---------|-------------|
| `show fsc workflow` | Display this guide |
| `load hara for [item]` | Import HARA safety goals |
| `derive all fsrs` | Create FSRs from all goals |
| `allocate fsrs` | Assign FSRs to components |
| `identify safety mechanisms` | Propose technical solutions |
| `check fsc compliance` | Verify ISO 26262-4 completeness |
| `generate fsc document` | Create final work product |

---

## ISO 26262-4:2018 Compliance

This workflow ensures compliance with:
- ✅ Clause 6.4.2: Derivation of functional safety requirements
- ✅ Clause 6.4.3: Functional safety requirements
- ✅ Clause 6.4.4: Allocation of functional safety requirements
- ✅ Clause 6.4.5: Technical safety requirements
- ✅ Clause 6.4.9: Traceability
- ✅ Clause 7.5: Work products (FSC document)

---

## Next Steps After FSC

1. **Technical Safety Concept** (ISO 26262-5)
   - Hardware safety requirements
   - Software safety requirements

2. **Product Development** (Parts 6-7)
   - Detailed hardware design
   - Software architecture and unit design

3. **Validation** (Part 4, Clause 8)
   - Functional safety validation plan
   - System integration and testing
"""
    
    return workflow


@tool(return_direct=True)
def load_hara_for_fsc(tool_input, cat):
    """
    Load HARA to begin FSC development.
    
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

**Please ensure:**
1. HARA has been generated using the HARA Assistant plugin
2. The item name matches exactly
3. The HARA is available in one of these locations:
   - Working memory (if just generated)
   - `hara_inputs/` folder in FSC plugin
   - Generated documents folder in HARA plugin

**Alternative:**
You can manually place your HARA file in:
- Excel format: `plugins/AI_Agent-FSC_Developer/hara_inputs/[item_name]_HARA.xlsx`
- Or use the HARA Assistant plugin to generate a new HARA

**Supported HARA Columns:**
- Hazard ID
- Function/Item
- Hazardous Event
- Operational Situation
- Severity (S), Exposure (E), Controllability (C)
- ASIL
- Safety Goal
- Safe State (optional)
- FTTI (optional)
"""
    
    # Parse and validate HARA data
    safety_goals = parse_safety_goals(hara_data)
    
    if not safety_goals:
        return f"""❌ **No valid safety goals found in HARA for '{item_name}'**

**Common issues:**
- HARA table missing safety goal column
- All safety goals are QM (no ASIL A/B/C/D)
- File format not recognized

**Please check:**
1. HARA file contains safety goals with ASIL ratings
2. At least one safety goal has ASIL A, B, C, or D
3. File is properly formatted (Excel or CSV with headers)
"""
    
    # Store in working memory
    cat.working_memory["fsc_safety_goals"] = safety_goals
    cat.working_memory["system_name"] = item_name
    cat.working_memory["fsc_stage"] = "hara_loaded"
    
    # Generate summary
    asil_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "QM": 0}
    for goal in safety_goals:
        asil = goal.get("asil", "QM")
        if asil in asil_counts:
            asil_counts[asil] += 1
    
    summary = f"""✅ **HARA Successfully Loaded for '{item_name}'**

**Safety Goals Summary:**
- Total Safety Goals: {len(safety_goals)}
- ASIL D: {asil_counts['D']} (Highest priority)
- ASIL C: {asil_counts['C']}
- ASIL B: {asil_counts['B']}
- ASIL A: {asil_counts['A']}
- QM: {asil_counts['QM']} (Not requiring FSC)

**Sample Safety Goals:**
"""
    
    # Show first 3 safety goals
    for i, goal in enumerate(safety_goals[:3], 1):
        summary += f"""
{i}. **{goal['id']}** (ASIL {goal['asil']})
   - **Goal:** {goal['goal']}
   - **Safe State:** {goal.get('safe_state', 'Not specified')}
   - **FTTI:** {goal.get('ftti', 'Not specified')}
"""
    
    if len(safety_goals) > 3:
        summary += f"\n... and {len(safety_goals) - 3} more safety goals"
    
    summary += """

---

**Next Steps:**

1. **Refine Safety Goals (if needed):**
   - `refine safety goal [SG-ID]` - Refine specific goal
   - `refine all safety goals` - Refine all at once

2. **Derive Functional Safety Requirements:**
   - `derive FSRs for [SG-ID]` - Derive for specific goal
   - `derive all FSRs` - Derive for all goals (recommended)

3. **View detailed goal:**
   - `show safety goal [SG-ID]` - Display full details

**ISO 26262-4:2018 Status:**
✅ Clause 6.4.1: Safety goals imported
⏳ Clause 6.4.2: FSR derivation (next step)
"""
    
    return summary


def find_hara_data(cat, item_name):
    """
    Find HARA data from various sources.
    Priority: working memory → hara_inputs/ → generated documents
    """
    
    # 1. Check working memory (from HARA plugin)
    if "hara_table" in cat.working_memory:
        log.info("✅ HARA found in working memory")
        return cat.working_memory["hara_table"]
    
    # 2. Check hara_inputs/ folder
    plugin_folder = os.path.dirname(__file__)
    hara_inputs_dir = os.path.join(plugin_folder, "hara_inputs")
    
    if os.path.exists(hara_inputs_dir):
        # Look for Excel files matching item name
        for filename in os.listdir(hara_inputs_dir):
            if item_name.lower().replace(" ", "_") in filename.lower():
                if filename.endswith(('.xlsx', '.xls')):
                    filepath = os.path.join(hara_inputs_dir, filename)
                    log.info(f"✅ HARA found: {filepath}")
                    return read_hara_excel(filepath)
    
    # 3. Check HARA plugin generated documents (if accessible)
    # This would require cross-plugin file access
    # For now, rely on user to place files in hara_inputs/
    
    log.warning(f"❌ No HARA data found for: {item_name}")
    return None


def read_hara_excel(filepath):
    """Read HARA table from Excel file."""
    if not EXCEL_AVAILABLE:
        log.error("openpyxl not available - cannot read Excel")
        return None
    
    try:
        workbook = openpyxl.load_workbook(filepath, data_only=True)
        sheet = workbook.active
        
        # Read headers (first row)
        headers = []
        for cell in sheet[1]:
            if cell.value:
                headers.append(str(cell.value).strip().lower())
        
        # Read data rows
        hara_rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0]:  # If first cell has value (Hazard ID)
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = value
                hara_rows.append(row_dict)
        
        log.info(f"✅ Read {len(hara_rows)} rows from HARA Excel")
        return hara_rows
        
    except Exception as e:
        log.error(f"Error reading HARA Excel: {e}")
        return None


def parse_safety_goals(hara_data):
    """
    Extract and validate safety goals from HARA data.
    Returns list of safety goal dictionaries.
    """
    
    safety_goals = []
    
    for i, row in enumerate(hara_data):
        # Look for safety goal in various possible column names
        goal_text = (
            row.get('safety goal') or 
            row.get('safety_goal') or 
            row.get('safetygoal') or 
            ""
        )
        
        asil = (
            row.get('asil') or 
            row.get('asil level') or 
            row.get('asil_level') or 
            "QM"
        )
        
        # Only include goals with ASIL (not QM)
        if goal_text and str(asil).upper() in ['A', 'B', 'C', 'D']:
            
            # Generate safety goal ID if not present
            goal_id = row.get('safety_goal_id') or row.get('sg_id') or f"SG-{i+1:03d}"
            
            safety_goals.append({
                "id": goal_id,
                "goal": goal_text,
                "asil": str(asil).upper(),
                "hazard": row.get('hazardous event', row.get('hazard', '')),
                "safe_state": row.get('safe state', row.get('safe_state', '')),
                "ftti": row.get('ftti', ''),
                "operational_situation": row.get('operational situation', ''),
                "source_row": i + 2  # Excel row number (1-indexed + header)
            })
    
    log.info(f"✅ Extracted {len(safety_goals)} safety goals with ASIL")
    return safety_goals


@tool(return_direct=False)
def show_safety_goal_details(tool_input, cat):
    """
    Display detailed information about a specific safety goal.
    
    Input: Safety goal ID (e.g., "SG-003")
    Example: "show safety goal SG-003"
    """
    
    goal_id = str(tool_input).strip().upper()
    
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    
    if not safety_goals:
        return "❌ No safety goals loaded. Use 'load HARA for [item]' first."
    
    # Find the goal
    goal = next((g for g in safety_goals if g['id'] == goal_id), None)
    
    if not goal:
        return f"❌ Safety goal '{goal_id}' not found. Available: {', '.join(g['id'] for g in safety_goals[:5])}..."
    
    details = f"""### Safety Goal Details: {goal['id']}

**ASIL Level:** {goal['asil']}

**Safety Goal Statement:**
{goal['goal']}

**Originating Hazard:**
{goal.get('hazard', 'Not specified')}

**Operational Situation:**
{goal.get('operational_situation', 'Not specified')}

**Safe State:**
{goal.get('safe_state', 'Not specified')}

**Fault-Tolerant Time Interval (FTTI):**
{goal.get('ftti', 'Not specified')}

**Source:** HARA row {goal.get('source_row', 'Unknown')}

---

**Actions Available:**
- `refine safety goal {goal_id}` - Improve goal statement
- `derive FSRs for {goal_id}` - Create functional requirements
- `show trace for {goal_id}` - View traceability
"""
    
    return details