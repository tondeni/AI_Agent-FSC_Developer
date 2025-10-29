# tools/workflow_tools.py
# Workflow guidance and help tools for FSC Developer

from cat.mad_hatter.decorators import tool
from cat.log import log


@tool(
    return_direct=True,
    examples=[
        "show FSC workflow",
        "help with FSC",
        "what are the FSC development steps",
        "how do I generate FSC"
    ]
)
def show_fsc_workflow(tool_input, cat):
    """
    Display the FSC development workflow per ISO 26262-3:2018, Clause 7.
    
    Shows complete step-by-step process for developing a Functional Safety Concept.
    
    Input: Any request for workflow, help, or guidance
    """
    
    log.info("📋 Displaying FSC workflow")
    
    workflow = """
# 📋 Functional Safety Concept (FSC) Development Workflow

*Per ISO 26262-3:2018, Clause 7*

---

## 🎯 Objectives (ISO 26262-3:2018, 7.1)

The FSC development aims to:

a) Specify functional/degraded behavior to achieve safety goals
b) Specify constraints for fault detection and control
c) Specify strategies to achieve fault tolerance
d) Allocate FSRs to system architectural design or external measures
e) Verify FSC and specify safety validation criteria

---

## 🔄 Complete Development Steps

### ➡️ **Step 1: Load HARA (Prerequisites)**
**Command:** `load HARA for [system name]`

**What it does:**
- Loads safety goals from HARA analysis
- Extracts ASIL ratings, safe states, FTTI
- Validates data per ISO 26262-3:2018, 7.3.1

**ISO Reference:** 7.3.1 (Prerequisites)

**Output:** Safety goals with ASIL, safe state, FTTI

---

### ➡️ **Step 2: Develop Safety Strategies**
**Command:** `develop safety strategy for all goals`

**What it does:**
- Generates 9 required strategies per safety goal:
  - a) Fault Avoidance
  - b) Fault Detection & Control
  - c) Safe State Transition
  - d) Fault Tolerance
  - e) Degradation
  - f) Driver Warning (Exposure)
  - g) Driver Warning (Controllability)
  - h) Timing Requirements
  - i) Arbitration

**ISO Reference:** 7.4.2.3

**Output:** Comprehensive safety strategies for each goal

---

### ➡️ **Step 3: Derive Functional Safety Requirements**
**Command:** `derive FSRs for all goals`
└─> **Export:** `export FSRs to excel` (review before allocation)

---

### ➡️ **Step 4: Allocate FSRs to Architecture**
**Command:** `allocate all FSRs`
└─> **Export:** `create excel file` (allocation matrix)

---

### ➡️ **Step 5: Identify Safety Mechanisms**
**Command:** `identify safety mechanisms`
- Identifies diagnostic mechanisms
- Defines redundancy strategies
- Maps mechanisms to FSRs
└─> **Export:** `export safety mechanisms to excel` (when available)

---
### ➡️ **Step 6: Specify Validation Criteria**
**Command:** `specify validation criteria`

---

### ➡️ **Step 7: Verify FSC**
**Command:** `verify FSC`

**What it does:**
- Verifies FSC completeness and correctness
- Checks consistency with safety goals
- Validates ability to mitigate hazards
- Generates verification report

**ISO Reference:** 7.4.4

**Output:** Verification report with compliance assessment

---

### ➡️ **Step 8: Generate FSC Documentation**
**Command:** `generate FSC document`

**What it does:**
- Creates complete FSC work product (Word document)
- Generates FSR traceability matrix (Excel)
- Includes all required sections per ISO 26262-3:2018, 7.5

**ISO Reference:** 7.5

**Output:** 
- FSC document (.docx)
- Traceability matrix (.xlsx)

---

## 📊 Work Products Generated (ISO 26262-3:2018, 7.5)

✅ **7.5.1:** Functional Safety Concept document
✅ **7.5.2:** Verification report of FSC
✅ **Traceability:** Safety Goals ↔ FSRs ↔ Architecture

---

## 🚀 Quick Start Example

```
1. load HARA for Battery Management System
2. develop safety strategy for all goals
3. derive FSRs for all goals
4. allocate all FSRs
5. specify validation criteria
6. verify FSC
7. generate FSC document
```

---

## 💡 Additional Commands

**View specific items:**
- `show safety goal SG-001`
- `show FSR FSR-001-DET-1`
- `show allocation summary`
- `show HARA statistics`

**Work with individual items:**
- `develop safety strategy for SG-003`
- `derive FSRs for SG-002`
- `allocate FSR-001-DET-1 to Voltage Monitor`

---

## ✅ ISO 26262-3:2018, Clause 7 Compliance

| Clause | Requirement | Tool Support |
|--------|-------------|--------------|
| 7.3.1 | Prerequisites (HARA) | ✅ Step 1 |
| 7.4.2.1 | FSR derivation | ✅ Step 3 |
| 7.4.2.2 | ≥1 FSR per goal | ✅ Validated |
| 7.4.2.3 | 9 strategies | ✅ Step 2 |
| 7.4.2.4 | FSR considerations | ✅ Step 3 |
| 7.4.2.8 | FSR allocation | ✅ Step 4 |
| 7.4.3 | Validation criteria | ✅ Step 5 |
| 7.4.4 | FSC verification | ✅ Step 6 |
| 7.5 | Work products | ✅ Step 7 |

---

## 🎓 Tips for Best Results

1. **Complete steps in order** - Each step builds on previous ones
2. **Review HARA first** - Ensure safety goals are complete and correct
3. **Iterate as needed** - You can regenerate strategies or FSRs if needed
4. **Validate continuously** - Check for issues after each major step
5. **Document assumptions** - Record any assumptions or constraints


**Ready to start?** Begin with: `load HARA for [your system name]`
"""
    
    return workflow


@tool(return_direct=True)
def show_fsc_status(tool_input, cat):
    """
    Show current FSC development status.
    
    Displays progress through the FSC workflow and identifies next steps.
    
    Input: "show status" or "where am I in the workflow"
    """
    
    log.info("📊 Checking FSC development status")
    
    # Check working memory for progress
    stage = cat.working_memory.get("fsc_stage", "not_started")
    system_name = cat.working_memory.get("system_name", "Unknown")
    
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    strategies = cat.working_memory.get("fsc_safety_strategies", [])
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    validation_criteria = cat.working_memory.get("fsc_validation_criteria", [])
    verification_report = cat.working_memory.get("fsc_verification_report", "")
    
    status = f"""# 📊 FSC Development Status

**System:** {system_name}
**Current Stage:** {stage.replace('_', ' ').title()}

---

## Progress Checklist

"""
    
    # Step 1: HARA loaded
    if safety_goals:
        status += f"✅ **Step 1: HARA Loaded** - {len(safety_goals)} safety goals\n"
    else:
        status += "⬜ **Step 1: HARA Loaded** - Not started\n"
        status += "   → Next: `load HARA for [system name]`\n"
    
    # Step 2: Strategies developed
    if strategies:
        status += f"✅ **Step 2: Safety Strategies** - {len(strategies)} strategies developed\n"
    elif safety_goals:
        status += "⬜ **Step 2: Safety Strategies** - Ready to start\n"
        status += "   → Next: `develop safety strategy for all goals`\n"
    else:
        status += "⬜ **Step 2: Safety Strategies** - Waiting for Step 1\n"
    
    # Step 3: FSRs derived
    if fsrs:
        status += f"✅ **Step 3: FSRs Derived** - {len(fsrs)} functional safety requirements\n"
    elif strategies:
        status += "⬜ **Step 3: FSRs Derived** - Ready to start\n"
        status += "   → Next: `derive FSRs for all goals`\n"
    else:
        status += "⬜ **Step 3: FSRs Derived** - Waiting for Step 2\n"
    
    # Step 4: FSRs allocated
    if fsrs:
        allocated = len([f for f in fsrs if f.get('allocated_to')])
        if allocated == len(fsrs):
            status += f"✅ **Step 4: FSRs Allocated** - All {len(fsrs)} FSRs allocated\n"
        elif allocated > 0:
            status += f"🔄 **Step 4: FSRs Allocated** - {allocated}/{len(fsrs)} FSRs allocated\n"
            status += "   → Next: `allocate all FSRs` to complete\n"
        else:
            status += "⬜ **Step 4: FSRs Allocated** - Ready to start\n"
            status += "   → Next: `allocate all FSRs`\n"
    else:
        status += "⬜ **Step 4: FSRs Allocated** - Waiting for Step 3\n"
    
    # Step 5: Validation criteria
    if validation_criteria:
        status += f"✅ **Step 5: Validation Criteria** - {len(validation_criteria)} criteria specified\n"
    elif fsrs and all(f.get('allocated_to') for f in fsrs):
        status += "⬜ **Step 5: Validation Criteria** - Ready to start\n"
        status += "   → Next: `specify validation criteria`\n"
    else:
        status += "⬜ **Step 5: Validation Criteria** - Waiting for Step 4\n"
    
    # Step 6: FSC verified
    if verification_report:
        status += "✅ **Step 6: FSC Verified** - Verification complete\n"
    elif validation_criteria:
        status += "⬜ **Step 6: FSC Verified** - Ready to start\n"
        status += "   → Next: `verify FSC`\n"
    else:
        status += "⬜ **Step 6: FSC Verified** - Waiting for Step 5\n"
    
    # Step 7: Document generated
    if stage == "document_generated":
        status += "✅ **Step 7: FSC Document** - Document generated\n"
    elif verification_report:
        status += "⬜ **Step 7: FSC Document** - Ready to generate\n"
        status += "   → Next: `generate FSC document`\n"
    else:
        status += "⬜ **Step 7: FSC Document** - Waiting for Step 6\n"
    
    status += "\n---\n\n"
    
    # Add statistics if data available
    if safety_goals:
        status += "## 📈 Statistics\n\n"
        status += f"- **Safety Goals:** {len(safety_goals)}\n"
        
        if strategies:
            status += f"- **Strategies:** {len(strategies)} (9 per goal)\n"
        
        if fsrs:
            status += f"- **FSRs:** {len(fsrs)}\n"
            asil_counts = {}
            for fsr in fsrs:
                asil = fsr.get('asil', 'Unknown')
                asil_counts[asil] = asil_counts.get(asil, 0) + 1
            
            status += "- **FSRs by ASIL:**\n"
            for asil in ['D', 'C', 'B', 'A']:
                if asil in asil_counts:
                    status += f"  - ASIL {asil}: {asil_counts[asil]}\n"
        
        if validation_criteria:
            status += f"- **Validation Criteria:** {len(validation_criteria)}\n"
    
    # Add completion percentage
    steps_completed = sum([
        bool(safety_goals),
        bool(strategies),
        bool(fsrs),
        bool(fsrs and all(f.get('allocated_to') for f in fsrs)),
        bool(validation_criteria),
        bool(verification_report),
        stage == "document_generated"
    ])
    
    completion = (steps_completed / 7) * 100
    
    status += f"\n**Overall Completion:** {completion:.0f}%\n"
    
    # Progress bar
    filled = int(completion / 10)
    bar = '█' * filled + '░' * (10 - filled)
    status += f"`{bar}` {completion:.0f}%\n"
    
    return status


@tool(return_direct=True)
def show_iso_26262_reference(tool_input, cat):
    """
    Show ISO 26262-3:2018 clause references for FSC development.
    
    Quick reference guide for ISO 26262 compliance.
    
    Input: "show ISO reference" or "ISO 26262 clauses"
    """
    
    reference = """# 📚 ISO 26262-3:2018 Reference Guide

## Clause 7: Functional Safety Concept

### 7.1 Objectives
Development of FSC to:
- Specify functional/degraded behavior per safety goals
- Specify fault detection and control constraints
- Specify fault tolerance strategies
- Allocate FSRs to architectural design
- Verify FSC and specify validation criteria

### 7.3.1 Prerequisites
Required inputs:
- Item definition (Clause 5)
- HARA report (Clause 6)
- System architectural design

### 7.4.2 Functional Safety Requirements

**7.4.2.1** - FSRs derived from safety goals
**7.4.2.2** - At least one FSR per safety goal
**7.4.2.3** - Strategies to achieve safety goals:
- a) Fault avoidance
- b) Fault detection and control
- c) Safe state transition
- d) Fault tolerance
- e) Degradation
- f) Warning (exposure reduction)
- g) Warning (controllability)
- h) Timing requirements
- i) Arbitration

**7.4.2.4** - FSRs shall consider:
- a) Operating modes
- b) Fault tolerant time interval
- c) Safe states
- d) Emergency operation time interval
- e) Functional redundancies

**7.4.2.5** - Safe state specification
**7.4.2.6** - Emergency operation specification
**7.4.2.7** - Driver actions specification
**7.4.2.8** - FSR allocation to elements

### 7.4.3 Safety Validation Criteria
Acceptance criteria for safety validation based on:
- Functional safety requirements
- Safety goals

### 7.4.4 Verification of FSC
Verify FSC per ISO 26262-8:2018, Clause 9 for:
- Consistency with safety goals
- Ability to mitigate hazards

### 7.5 Work Products
**7.5.1** - Functional safety concept
**7.5.2** - Verification report of FSC

---

## Related Standards

**ISO 26262-4:2018, Clause 8** - Safety Validation
**ISO 26262-8:2018, Clause 6** - Requirements specification
**ISO 26262-8:2018, Clause 9** - Verification methods
**ISO 26262-9:2018, Clause 5** - ASIL decomposition

---

**Tip:** Reference these clauses in your FSC documentation for traceability.
"""
    
    return reference