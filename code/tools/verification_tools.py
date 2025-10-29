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
    return_direct=True,
    examples=[
        "specify validation criteria",
        "define validation criteria",
        "create validation plan"
    ]
)
def specify_safety_validation_criteria(tool_input, cat):
    """
    Specify validation criteria for safety goals and FSRs.
    
    Per ISO 26262-3:2018, Clause 7.4.3.
    """
    
    log.info("🔧 TOOL CALLED: specify_safety_validation_criteria")
    
    # Get data
    goals = cat.working_memory.get('fsc_safety_goals', [])
    fsrs = cat.working_memory.get('fsc_functional_requirements', [])
    system_name = cat.working_memory.get('system_name', 'System')
    
    if not goals or not fsrs:
        return "Error: Need both safety goals and FSRs. Please complete previous steps first."
    
    try:
        # Import validation generator
        from ..generators.validation_generator import ValidationGenerator
        
        # Generate validation criteria
        generator = ValidationGenerator(llm_function=cat.llm)
        criteria = generator.generate_validation_criteria(goals, fsrs, system_name)
        
        # Store in working memory
        cat.working_memory['fsc_validation_criteria'] = criteria
        cat.working_memory['fsc_stage'] = 'validation_criteria_specified'
        cat.working_memory['needs_formatting'] = True
        cat.working_memory['last_operation'] = 'validation_criteria_specification'
        
        # ✅ SIMPLE PLAIN TEXT OUTPUT
        output = f"Successfully specified validation criteria for {system_name}.\n\n"
        output += f"Defined {len(criteria)} validation criteria for {len(goals)} safety goals and {len(fsrs)} FSRs.\n"
        output += "Criteria follow ISO 26262-3:2018, Clause 7.4.3 requirements.\n\n"
        
        # List criteria in simple format
        for criterion in criteria:
            output += f"{criterion['id']}: {criterion['description']}\n"
            output += f"  Reference: {criterion['reference']}\n"
            output += f"  Test Method: {criterion['method']}\n"
            output += f"  Acceptance: {criterion['acceptance']}\n"
            output += f"  Level: {criterion['level']}\n"
            output += "\n"
        
        log.info(f"✅ Specified {len(criteria)} validation criteria")
        
        return output
        
    except Exception as e:
        log.error(f"Error specifying validation criteria: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"Error specifying validation criteria: {str(e)}"


# @tool(
#     return_direct=True,
#     examples=[
#         "verify FSC",
#         "check FSC completeness",
#         "validate functional safety concept"
#     ]
# )
# def verify_functional_safety_concept(tool_input, cat):
#     """
#     Verify FSC completeness and ISO 26262 compliance.
    
#     Per ISO 26262-3:2018, Clause 7.4.4.
#     """
    
#     log.info("🔧 TOOL CALLED: verify_functional_safety_concept")
    
#     # Get data
#     goals = cat.working_memory.get('fsc_safety_goals', [])
#     strategies = cat.working_memory.get('fsc_safety_strategies', [])
#     fsrs = cat.working_memory.get('fsc_functional_requirements', [])
#     allocation = cat.working_memory.get('fsc_allocation_matrix', {})
#     validation = cat.working_memory.get('fsc_validation_criteria', [])
#     system_name = cat.working_memory.get('system_name', 'System')
    
#     if not all([goals, strategies, fsrs]):
#         return "Error: Incomplete FSC data. Please complete all previous steps:\n" \
#                "1. Load HARA\n" \
#                "2. Develop strategies\n" \
#                "3. Derive FSRs\n" \
#                "4. Allocate FSRs\n" \
#                "5. Specify validation criteria"
    
#     try:
#         # Import verifier
#         from ..validators.fsc_verifier import FSCVerifier
        
#         # Perform verification
#         verifier = FSCVerifier()
#         verification_result = verifier.verify_fsc(goals, strategies, fsrs, allocation, validation)
        
#         # Store result
#         cat.working_memory['fsc_verification_report'] = verification_result
#         cat.working_memory['fsc_stage'] = 'fsc_verified'
#         cat.working_memory['last_operation'] = 'fsc_verification'
        
#         # ✅ SIMPLE PLAIN TEXT OUTPUT
#         output = f"FSC Verification Report for {system_name}\n"
#         output += "=" * 60 + "\n\n"
        
#         output += f"Overall Status: {verification_result['status']}\n\n"
        
#         output += "Verification Checks:\n"
#         for check in verification_result['checks']:
#             status = "PASS" if check['passed'] else "FAIL"
#             output += f"  [{status}] {check['name']}: {check['message']}\n"
        
#         output += "\nCompleteness:\n"
#         output += f"  Safety Goals: {len(goals)}\n"
#         output += f"  Safety Strategies: {len(strategies)}\n"
#         output += f"  FSRs: {len(fsrs)}\n"
#         output += f"  Allocated FSRs: {len([f for f in fsrs if f.get('allocated_to') != 'TBD'])}\n"
#         output += f"  Validation Criteria: {len(validation)}\n"
        
#         output += "\nISO 26262-3:2018 Compliance:\n"
#         for clause in verification_result['iso_compliance']:
#             status = "✓" if clause['compliant'] else "✗"
#             output += f"  {status} Clause {clause['clause']}: {clause['requirement']}\n"
        
#         if verification_result['recommendations']:
#             output += "\nRecommendations:\n"
#             for rec in verification_result['recommendations']:
#                 output += f"  - {rec}\n"
        
#         log.info(f"✅ FSC verification complete: {verification_result['status']}")
        
#         return output
        
#     except Exception as e:
#         log.error(f"Error verifying FSC: {e}")
#         import traceback
#         log.error(traceback.format_exc())
#         return f"Error verifying FSC: {str(e)}"


# @tool(
#     return_direct=False,
#     examples=[
#         "show validation criteria",
#         "list validation criteria",
#         "display acceptance criteria",
#         "validation criteria overview"
#     ]
# )
# def show_validation_criteria_summary(tool_input, cat):
#     """DISPLAY TOOL: Shows summary of ALL validation criteria.
    
#     Use when user wants to VIEW/SEE existing validation criteria summary.
#     Shows statistics and distribution of criteria.
    
#     Trigger phrases: "show validation criteria", "list criteria", "criteria overview"
#     NOT for: creating criteria, performing verification, or verification reports
    
#     Displays: Total criteria, distribution by method, coverage by goal/FSR
#     Prerequisites: Validation criteria must be specified first
#     Input: Not required
#     """
    
#     log.warning(f"----------------✅ TOOL CALLED: show_validation_criteria_summary with input {tool_input} ----------------")
    
#     validation_criteria_data = cat.working_memory.get("fsc_validation_criteria", [])
#     system_name = cat.working_memory.get("system_name", "Unknown System")
    
#     if not validation_criteria_data:
#         # ✅ Return string directly
#         return "❌ No validation criteria specified yet. Use: `specify validation criteria`"
    
#     # Calculate statistics
#     total = len(validation_criteria_data)
#     by_method = {}
#     by_goal = {}
#     goal_level = 0
#     fsr_level = 0
    
#     for criteria in validation_criteria_data:
#         # Count by method
#         method = criteria.get('method', 'Unknown')
#         by_method[method] = by_method.get(method, 0) + 1
        
#         # Count by goal
#         sg_id = criteria.get('safety_goal_id', 'Unknown')
#         by_goal[sg_id] = by_goal.get(sg_id, 0) + 1
        
#         # Count level
#         if criteria.get('fsr_id'):
#             fsr_level += 1
#         else:
#             goal_level += 1
    
#     # ✅ Return string directly with formatted summary
#     output = f"""📊 **Validation Criteria Summary for {system_name}**

# **Total Criteria:** {total}

# **Criteria Coverage:**
# - Goal-Level Criteria: {goal_level}
# - FSR-Level Criteria: {fsr_level}

# **Distribution by Validation Method:**
# """
    
#     for method, count in sorted(by_method.items(), key=lambda x: x[1], reverse=True):
#         output += f"- {method}: {count} criteria\n"
    
#     output += f"\n**Distribution by Safety Goal:**\n"
#     for sg_id, count in sorted(by_goal.items()):
#         output += f"- {sg_id}: {count} criteria\n"
    
#     output += "\n\n**Commands:**"
#     output += "\n- Verify FSC: `verify FSC`"
#     output += "\n- Generate document: `generate FSC document`"
    
#     log.info(f"📊 Showed validation criteria summary: {total} criteria")
    
#     return output


# @tool(
#     return_direct=False,
#     examples=[
#         "show verification report",
#         "display FSC verification report",
#         "show verification results"
#     ]
# )
# def show_verification_report(tool_input, cat):
#     """REPORT DISPLAY TOOL: Displays the FSC verification report.
    
#     Use when user wants to VIEW the previously generated verification report.
    
#     Trigger phrases: "show verification report", "display verification results"
#     NOT for: performing verification, creating criteria, or criteria summary
    
#     Displays: Complete verification report with pass/fail status
#     Prerequisites: FSC must be verified first using verify_functional_safety_concept
#     Input: Not required
#     """
    
#     log.warning(f"----------------✅ TOOL CALLED: show_verification_report with input {tool_input} ----------------")
    
#     verification_report = cat.working_memory.get("fsc_verification_report")
    
#     if not verification_report:
#         # ✅ Return string directly
#         return "❌ No verification report available. Please verify FSC first: `verify FSC`"
    
#     log.info("📋 Displayed verification report")
    
#     # ✅ Return string directly
#     return verification_report