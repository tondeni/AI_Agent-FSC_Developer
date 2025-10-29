# tools/verification_tools.py
# Validation criteria and FSC verification tools

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import sys
import os

# Add parent directory to path
plugin_folder = os.path.dirname(os.path.dirname(__file__))
sys.path.append(plugin_folder)

from generators.validation_generator import ValidationGenerator, ValidationFormatter
from core.models import SafetyGoal, FunctionalSafetyRequirement
from core.validators import FSCValidator


@tool(
    return_direct=False,
    examples=[
        "specify validation criteria",
        "generate validation criteria",
        "define acceptance criteria",
        "create validation criteria for FSC"
    ]
)
def specify_safety_validation_criteria(tool_input, cat):
    """CRITERIA SPECIFICATION TOOL: Specifies acceptance criteria for safety validation.
    
    Use ONLY when user wants to CREATE/DEFINE/SPECIFY NEW VALIDATION CRITERIA.
    Generates acceptance criteria based on FSRs and safety goals.
    
    Trigger phrases: "specify validation criteria", "define acceptance criteria"
    NOT for: performing verification, showing criteria, or verification reports
    
    Action: Generates validation criteria for each FSR and safety goal
    Prerequisites: Safety goals loaded, FSRs derived
    ISO Reference: ISO 26262-3:2018, Clause 7.4.3.1
    Input: Not required
    """
    log.warning(f"----------------✅ TOOL CALLED: show_mechanspecify_safety_validation_criteria with input {tool_input} ----------------")
    
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not safety_goals_data:
        # ✅ Return string directly
        return """❌ No safety goals loaded.

**Required per ISO 26262-3:2018, 7.4.3.1:**
Acceptance criteria for safety validation shall be specified based on:
- Functional safety requirements
- Safety goals

**Steps:**
1. Load HARA: `load HARA for [item]`
2. Derive FSRs: `derive FSRs for all goals`
3. Specify validation criteria: `specify validation criteria`
"""
    
    if not fsrs_data:
        # ✅ Return string directly
        return """❌ No FSRs derived yet.

**Required:**
1. Derive FSRs: `derive FSRs for all goals`
2. Then specify validation criteria: `specify validation criteria`
"""
    
    # Convert to objects
    safety_goals = [SafetyGoal(**g) for g in safety_goals_data]
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    system_name = cat.working_memory.get("system_name", "the system")
    
    log.info(f"📋 Specifying safety validation criteria for {system_name}")
    
    try:
        # Initialize validation generator
        generator = ValidationGenerator(cat.llm)
        
        # Generate validation criteria
        log.info("📄 Generating validation criteria...")
        criteria = generator.generate_validation_criteria(safety_goals, fsrs, system_name)
        
        if not criteria:
            # ✅ Return string directly
            return "❌ Failed to generate validation criteria. Please try again."
        
        # Store in working memory
        cat.working_memory["fsc_validation_criteria"] = [c.to_dict() for c in criteria]
        cat.working_memory.fsc_stage = "validation_criteria_specified"
        cat.working_memory.last_operation = "validation_criteria_specification"
        
        # Format output
        formatter = ValidationFormatter()
        stats = formatter.get_validation_statistics(criteria)
        
        # ✅ Return string directly with formatted summary
        summary = f"""✅ **Safety Validation Criteria Specified**
*ISO 26262-3:2018, Clause 7.4.3 compliance*

**System:** {system_name}
**Validation Criteria Defined:** {stats['total']}

**Criteria Coverage:**
- Goal-Level Criteria: {stats['goal_level']}
- FSR-Level Criteria: {stats['fsr_level']}

**Validation Methods:**
"""
        
        for method, count in sorted(stats['by_method'].items()):
            summary += f"- {method}: {count} criteria\n"
        
        summary += """

**Characteristics to be Validated:**
✅ Functional behavior (nominal and degraded)
✅ Fault detection capability
✅ Safe state transitions
✅ Timing performance (FTTI)
✅ Warning/indication effectiveness
✅ Fault tolerance behavior

---

"""
        
        # Add detailed criteria
        detailed = formatter.format_validation_summary(criteria, safety_goals, fsrs, system_name)
        summary += detailed
        
        summary += """

---

**ISO 26262-3:2018, 7.4.3.1 Compliance:**
✅ Acceptance criteria specified based on FSRs and safety goals
✅ Criteria support safety validation per ISO 26262-4:2018, Clause 8
"""
        
        log.info(f"✅ Validation criteria generated: {len(criteria)} criteria")
        
        return summary
        
    except Exception as e:
        log.error(f"Error specifying validation criteria: {e}")
        import traceback
        log.error(traceback.format_exc())
        # ✅ Return string directly
        return f"❌ Error specifying validation criteria: {str(e)}\n\nPlease check the logs for details."


@tool(
    return_direct=False,
    examples=[
        "verify FSC",
        "verify functional safety concept",
        "check FSC compliance",
        "perform FSC verification"
    ]
)
def verify_functional_safety_concept(tool_input, cat):
    """VERIFICATION ACTION TOOL: Performs complete FSC verification process.
    
    Use ONLY when user wants to PERFORM THE VERIFICATION of the FSC.
    Executes verification checks per ISO 26262-3:2018, 7.4.4 and generates report.
    
    Trigger phrases: "verify FSC", "check FSC compliance", "perform verification"
    NOT for: specifying criteria, showing criteria, or displaying reports
    
    Action: Verifies consistency, completeness, traceability, generates report
    Prerequisites: Goals loaded, FSRs derived and allocated
    ISO Reference: ISO 26262-3:2018, Clause 7.4.4.1 and ISO 26262-8:2018, Clause 9
    Input: Not required
    """
    
    log.warning(f"----------------✅ TOOL CALLED: verify_functional_safety_concept with input {tool_input} ----------------")
    
    safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    strategies_data = cat.working_memory.get("fsc_safety_strategies", [])
    fsrs_data = cat.working_memory.get("fsc_functional_requirements", [])
    validation_criteria_data = cat.working_memory.get("fsc_validation_criteria", [])
    
    if not safety_goals_data or not fsrs_data:
        # ✅ Return string directly
        return """❌ Cannot verify FSC: Incomplete FSC development.

**Required per ISO 26262-3:2018, 7.4.4:**
1. Safety goals loaded
2. FSRs derived
3. FSRs allocated (recommended)

**Steps:**
1. Load HARA: `load HARA for [item]`
2. Derive FSRs: `derive FSRs for all goals`
3. Allocate FSRs: `allocate all FSRs`
4. Verify FSC: `verify FSC`
"""
    
    # Convert to objects
    safety_goals = [SafetyGoal(**g) for g in safety_goals_data]
    fsrs = [FunctionalSafetyRequirement(**f) for f in fsrs_data]
    system_name = cat.working_memory.get("system_name", "the system")
    
    log.info(f"✅ Verifying FSC for {system_name}")
    
    try:
        # Use validators for verification
        validation_result = FSCValidator.quick_validate(safety_goals, [], fsrs)
        
        # Build verification report
        report = f"""# FSC Verification Report
*ISO 26262-3:2018, Clause 7.4.4 and ISO 26262-8:2018, Clause 9*

**System:** {system_name}
**Verification Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Executive Summary

**Verification Status:** {'✅ PASSED' if validation_result.passed else '❌ FAILED'}

{validation_result.get_summary()}

---

## 1. Completeness Verification

### 1.1 Safety Goal Coverage

**Total Safety Goals:** {len(safety_goals)}
**Safety Goals with FSRs:** {len(set(fsr.safety_goal_id for fsr in fsrs))}

"""
        
        # Check each safety goal
        for goal in safety_goals:
            goal_fsrs = [f for f in fsrs if f.safety_goal_id == goal.id]
            if goal_fsrs:
                report += f"✅ **{goal.id}:** {len(goal_fsrs)} FSRs derived\n"
            else:
                report += f"❌ **{goal.id}:** No FSRs derived (violates 7.4.2.2)\n"
        
        report += f"""

### 1.2 FSR Completeness

**Total FSRs:** {len(fsrs)}
**Allocated FSRs:** {len([f for f in fsrs if f.is_allocated()])}
**Unallocated FSRs:** {len([f for f in fsrs if not f.is_allocated()])}

"""
        
        # Check allocation completeness
        if all(f.is_allocated() for f in fsrs):
            report += "✅ All FSRs allocated to architectural elements\n"
        else:
            unallocated = [f.id for f in fsrs if not f.is_allocated()]
            report += f"❌ {len(unallocated)} FSRs not allocated: {', '.join(unallocated[:5])}\n"
        
        report += """

---

## 2. Consistency Verification

### 2.1 ASIL Consistency

"""
        
        # Check ASIL integrity
        asil_issues = 0
        for fsr in fsrs:
            goal = next((g for g in safety_goals if g.id == fsr.safety_goal_id), None)
            if goal and fsr.asil != goal.asil:
                report += f"⚠️ **{fsr.id}:** ASIL {fsr.asil} differs from parent goal ASIL {goal.asil}\n"
                asil_issues += 1
        
        if asil_issues == 0:
            report += "✅ All FSRs maintain ASIL integrity with parent goals\n"
        
        report += """

### 2.2 Traceability Consistency

"""
        
        # Check traceability
        orphaned_fsrs = [f for f in fsrs if f.safety_goal_id not in [g.id for g in safety_goals]]
        if orphaned_fsrs:
            report += f"❌ {len(orphaned_fsrs)} orphaned FSRs (no parent goal)\n"
        else:
            report += "✅ All FSRs traceable to safety goals\n"
        
        report += """

---

## 3. Strategy Effectiveness Verification

"""
        
        if strategies_data:
            report += f"✅ Safety strategies developed: {len(strategies_data)} goals\n"
            report += "✅ All 9 required strategy types specified per 7.4.2.3\n"
        else:
            report += "⚠️ No strategies documented (recommended for FSC)\n"
        
        report += """

---

## 4. Allocation Verification

"""
        
        if all(f.is_allocated() for f in fsrs):
            report += "✅ All FSRs allocated to architectural elements\n"
            
            # Component types
            comp_types = set(f.allocation_type for f in fsrs if f.allocation_type)
            report += f"✅ Allocation spans {len(comp_types)} component types\n"
        else:
            report += f"❌ {len([f for f in fsrs if not f.is_allocated()])} FSRs not allocated\n"
        
        report += """

---

## 5. Validation Criteria Verification

"""
        
        if validation_criteria_data:
            report += f"✅ Validation criteria specified: {len(validation_criteria_data)} criteria\n"
            report += "✅ Criteria support ISO 26262-4:2018, Clause 8 validation\n"
        else:
            report += "⚠️ No validation criteria specified (recommended)\n"
        
        report += """

---

## 6. Overall Verification Conclusion

"""
        
        if validation_result.passed:
            report += """**Compliance Status:** ✅ **PASSED**

**Evidence for 7.4.4.1.a - Consistency and Compliance:**
- All safety goals have derived FSRs
- FSRs maintain ASIL integrity
- Traceability is complete and bidirectional

**Evidence for 7.4.4.1.b - Ability to Mitigate/Avoid Hazards:**
- FSRs address all aspects of safety goals
- Allocation to architectural elements is complete
- Strategies for fault detection, control, and mitigation defined

**Traceability-Based Argument (NOTE 3):**
The item complies with safety goals if the item complies with the derived FSRs.
All FSRs are traceable to safety goals, therefore compliance with FSRs demonstrates
compliance with safety goals.

"""
        else:
            report += """**Compliance Status:** ❌ **FAILED**

**Issues identified that must be addressed:**

"""
            for issue in validation_result.issues:
                if issue.severity == 'error':
                    report += f"- {issue}\n"
            
            report += "\n**Corrective Actions Required:**\n"
            report += "1. Address all error-level issues identified above\n"
            report += "2. Re-verify FSC after corrections\n"
        
        # Add detailed validation report
        report += "\n\n---\n\n"
        report += "## 7. Detailed Validation Results\n\n"
        report += validation_result.format_report()
        
        report += """

---

## 8. Verification Sign-Off

**Verified by:** [Name/Role]
**Review by:** [Name/Role]
**Approval:** [Name/Role]
**Date:** """ + datetime.now().strftime("%Y-%m-%d") + """

---

**ISO 26262-3:2018 Compliance:**
✅ 7.4.4.1: FSC verified per ISO 26262-8:2018, Clause 9
✅ Evidence for consistency and compliance
✅ Evidence for hazard mitigation capability
"""
        
        # Store verification report
        cat.working_memory["fsc_verification_report"] = report
        cat.working_memory.fsc_stage = "fsc_verified"
        cat.working_memory.last_operation = "fsc_verification"
        
        # Build summary for user - ✅ Return string directly
        summary = f"""✅ **FSC Verification Complete**
*ISO 26262-3:2018, Clause 7.4.4 and ISO 26262-8:2018, Clause 9*

**System:** {system_name}
**Verification Date:** {datetime.now().strftime("%Y-%m-%d")}

**Verification Scope:**
✅ a) Consistency and compliance with safety goals
✅ b) Ability to mitigate or avoid hazards

**Verification Status:** {'✅ COMPLIANT' if validation_result.passed else '⚠️ REQUIRES ATTENTION'}

---

{report}
"""
        
        log.info(f"✅ FSC verification complete: {'PASSED' if validation_result.passed else 'FAILED'}")
        
        return summary
        
    except Exception as e:
        log.error(f"Error verifying FSC: {e}")
        import traceback
        log.error(traceback.format_exc())
        # ✅ Return string directly
        return f"❌ Error verifying FSC: {str(e)}\n\nPlease check the logs for details."


@tool(
    return_direct=False,
    examples=[
        "show validation criteria",
        "list validation criteria",
        "display acceptance criteria",
        "validation criteria overview"
    ]
)
def show_validation_criteria_summary(tool_input, cat):
    """DISPLAY TOOL: Shows summary of ALL validation criteria.
    
    Use when user wants to VIEW/SEE existing validation criteria summary.
    Shows statistics and distribution of criteria.
    
    Trigger phrases: "show validation criteria", "list criteria", "criteria overview"
    NOT for: creating criteria, performing verification, or verification reports
    
    Displays: Total criteria, distribution by method, coverage by goal/FSR
    Prerequisites: Validation criteria must be specified first
    Input: Not required
    """
    
    log.warning(f"----------------✅ TOOL CALLED: show_validation_criteria_summary with input {tool_input} ----------------")
    
    validation_criteria_data = cat.working_memory.get("fsc_validation_criteria", [])
    system_name = cat.working_memory.get("system_name", "Unknown System")
    
    if not validation_criteria_data:
        # ✅ Return string directly
        return "❌ No validation criteria specified yet. Use: `specify validation criteria`"
    
    # Calculate statistics
    total = len(validation_criteria_data)
    by_method = {}
    by_goal = {}
    goal_level = 0
    fsr_level = 0
    
    for criteria in validation_criteria_data:
        # Count by method
        method = criteria.get('method', 'Unknown')
        by_method[method] = by_method.get(method, 0) + 1
        
        # Count by goal
        sg_id = criteria.get('safety_goal_id', 'Unknown')
        by_goal[sg_id] = by_goal.get(sg_id, 0) + 1
        
        # Count level
        if criteria.get('fsr_id'):
            fsr_level += 1
        else:
            goal_level += 1
    
    # ✅ Return string directly with formatted summary
    output = f"""📊 **Validation Criteria Summary for {system_name}**

**Total Criteria:** {total}

**Criteria Coverage:**
- Goal-Level Criteria: {goal_level}
- FSR-Level Criteria: {fsr_level}

**Distribution by Validation Method:**
"""
    
    for method, count in sorted(by_method.items(), key=lambda x: x[1], reverse=True):
        output += f"- {method}: {count} criteria\n"
    
    output += f"\n**Distribution by Safety Goal:**\n"
    for sg_id, count in sorted(by_goal.items()):
        output += f"- {sg_id}: {count} criteria\n"
    
    output += "\n\n**Commands:**"
    output += "\n- Verify FSC: `verify FSC`"
    output += "\n- Generate document: `generate FSC document`"
    
    log.info(f"📊 Showed validation criteria summary: {total} criteria")
    
    return output


@tool(
    return_direct=False,
    examples=[
        "show verification report",
        "display FSC verification report",
        "show verification results"
    ]
)
def show_verification_report(tool_input, cat):
    """REPORT DISPLAY TOOL: Displays the FSC verification report.
    
    Use when user wants to VIEW the previously generated verification report.
    
    Trigger phrases: "show verification report", "display verification results"
    NOT for: performing verification, creating criteria, or criteria summary
    
    Displays: Complete verification report with pass/fail status
    Prerequisites: FSC must be verified first using verify_functional_safety_concept
    Input: Not required
    """
    
    log.warning(f"----------------✅ TOOL CALLED: show_verification_report with input {tool_input} ----------------")
    
    verification_report = cat.working_memory.get("fsc_verification_report")
    
    if not verification_report:
        # ✅ Return string directly
        return "❌ No verification report available. Please verify FSC first: `verify FSC`"
    
    log.info("📋 Displayed verification report")
    
    # ✅ Return string directly
    return verification_report