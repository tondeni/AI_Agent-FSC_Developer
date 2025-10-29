# tools/hara_tools.py
# HARA loading and viewing tools

from cat.mad_hatter.decorators import tool
from cat.log import log
import sys
import os
from loaders.hara_loader import HARALoader
from core.models import SafetyGoal
from core.validators import validate_safety_goals
from utils.file_utils import find_hara_files
import os


# Add parent directory to path
plugin_folder = os.path.dirname(os.path.dirname(__file__))
sys.path.append(plugin_folder)


# @tool(
#     return_direct=True,
#     examples=[
#         "load HARA for Battery Management System",
#         "load HARA for Electric Power Steering",
#         "extract safety goals from HARA",
#         "use current HARA"
#     ]
# )
# def load_hara_for_fsc(tool_input, cat):
#     """
#     Load HARA outputs to begin FSC development.
    
#     Per ISO 26262-3:2018, 7.3.1: Prerequisites
#     - Item definition (ISO 26262-3, Clause 5)
#     - HARA report (ISO 26262-3, Clause 6)
#     - System architectural design (external source)
    
#     Extracts:
#     - Item/System name
#     - Safety Goals
#     - ASIL ratings
#     - Safe States
#     - FTTI (Fault Tolerant Time Interval)
    
#     Sources (priority order):
#     1. Working memory (if chained from HARA plugin)
#     2. hara_inputs/ folder (uploaded files)
#     3. Generated documents from HARA plugin
    
#     Input: Item name or "use current HARA"
#     Example: "load HARA for Battery Management System"
#     """
    
#     log.info("🔥 TOOL CALLED: load_hara_for_fsc")
    
#     # Parse input
#     item_name = "Unknown System"
#     if isinstance(tool_input, str):
#         item_name = tool_input.strip()
#         if item_name.lower() in ["use current hara", "use current", "current", ""]:
#             item_name = cat.working_memory.get("system_name", item_name)
#         # Remove common prefixes
#         item_name = item_name.replace("load hara for", "").replace("load hara", "").strip()
#     elif isinstance(tool_input, dict):
#         item_name = tool_input.get("item_name", item_name)
    
#     log.info(f"📥 Loading HARA for: {item_name}")
    
#     # Initialize loader
#     loader = HARALoader(plugin_folder)
    
#     # Find and load HARA data
#     hara_data = loader.load_hara(item_name, cat)
    
#     # Check what find_hara_files returns
#     files = find_hara_files()
#     log.warning(f"Found HARA files: {files}")

#     if not hara_data:
#         return f"""❌ **No HARA found for '{item_name}'**

# **ISO 26262-3:2018, 7.3.1 Prerequisites:**
# The following information shall be available:
# - Item definition (ISO 26262-3, Clause 5)
# - HARA report (ISO 26262-3, Clause 6)
# - System architectural design

# **Please ensure:**
# 1. HARA has been generated using the HARA Assistant plugin
# 2. The item name matches exactly
# 3. The HARA is available in one of these locations:
#    - Working memory (if just generated)
#    - `hara_inputs/` folder in FSC plugin
#    - Generated documents from HARA plugin

# **Alternative:**
# You can manually place your HARA file in:
# - Excel format: `plugins/AI_Agent-FSC_Developer/hara_inputs/{item_name}_HARA.xlsx`

# **Supported HARA Columns:**
# - Safety Goal (required)
# - ASIL (required - A/B/C/D)
# - Safe State (optional)
# - FTTI (optional)
# - Hazard ID, Severity (S), Exposure (E), Controllability (C) (optional)
# """
    
#     # Validate safety goals
#     validation_result = validate_safety_goals(hara_data.goals)
    
#     if not validation_result.passed:
#         log.warning(f"⚠️ HARA validation found issues")
#         issues_summary = "\n".join([str(i) for i in validation_result.issues if i.severity == 'error'])
#         return f"""⚠️ **HARA loaded but has validation issues**

# {validation_result.format_report()}

# **Please review and address errors before proceeding.**
# """
    
#     # Store in working memory
#     cat.working_memory.system_name = hara_data.system
#     cat.working_memory.fsc_safety_goals = [goal.to_dict() for goal in hara_data.goals]
#     cat.working_memory.fsc_stage = "hara_loaded"
    
#     # Generate summary
#     summary = _build_hara_summary(hara_data, validation_result)
    
#     log.info(f"✅ HARA loaded: {len(hara_data.goals)} safety goals")
    
#     return summary


# @tool(return_direct=True)
# def show_safety_goal_details(tool_input, cat):
#     """
#     Show detailed information for a specific safety goal.
    
#     Input: Safety goal ID (e.g., "SG-001")
#     Example: "show safety goal SG-001"
#     """
    
#     safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
    
#     if not safety_goals_data:
#         return "❌ No safety goals loaded. Load HARA first: `load HARA for [system name]`"
    
#     # Parse input to get SG ID
#     sg_id = str(tool_input).strip().upper()
#     sg_id = sg_id.replace("SHOW SAFETY GOAL", "").replace("SAFETY GOAL", "").strip()
#     if not sg_id.startswith('SG-'):
#         sg_id = 'SG-' + sg_id.replace('SG', '').replace('-', '').strip()
    
#     # Find the safety goal
#     goal_data = next((g for g in safety_goals_data if g['id'] == sg_id), None)
    
#     if not goal_data:
#         available = ', '.join([g['id'] for g in safety_goals_data[:5]])
#         return f"""❌ Safety Goal '{sg_id}' not found.

# **Available Safety Goals:** {available}{'...' if len(safety_goals_data) > 5 else ''}

# **Usage:** `show safety goal SG-001`
# """
    
#     # Build detailed view
#     details = f"""## 📋 Safety Goal Details: {sg_id}

# **Safety Goal:**
# {goal_data.get('description', 'Not specified')}

# **Risk Assessment:**
# - **ASIL:** {goal_data.get('asil', 'Unknown')}
# - **Severity (S):** {goal_data.get('severity', 'Not specified')}
# - **Exposure (E):** {goal_data.get('exposure', 'Not specified')}
# - **Controllability (C):** {goal_data.get('controllability', 'Not specified')}

# **Safety Requirements:**
# - **Safe State:** {goal_data.get('safe_state', 'To be specified per ISO 26262-3:2018, 7.4.2.5')}
# - **FTTI:** {goal_data.get('ftti', 'To be determined per ISO 26262-3:2018, 7.4.2.4.b')}

# **Traceability:**
# - **Hazard ID:** {goal_data.get('hazard_id', 'Not specified')}
# - **Hazardous Event:** {goal_data.get('hazardous_event', 'Not specified')}
# - **Operational Situation:** {goal_data.get('operational_situation', 'Not specified')}

# ---

# **Next Steps:**
# - Develop strategy: `develop safety strategy for {sg_id}`
# - Or develop all: `develop safety strategy for all goals`
# """
    
#     return details


# @tool(return_direct=True)
# def show_hara_statistics(tool_input, cat):
#     """
#     Show statistical summary of loaded HARA.
    
#     Input: "show HARA statistics"
#     """
    
#     safety_goals_data = cat.working_memory.get("fsc_safety_goals", [])
#     system_name = cat.working_memory.get("system_name", "Unknown System")
    
#     if not safety_goals_data:
#         return "❌ No HARA loaded. Load HARA first: `load HARA for [system name]`"
    
#     # Calculate statistics
#     total = len(safety_goals_data)
    
#     # ASIL distribution
#     asil_dist = {}
#     for goal in safety_goals_data:
#         asil = goal.get('asil', 'Unknown')
#         asil_dist[asil] = asil_dist.get(asil, 0) + 1
    
#     # Safe state specification status
#     safe_states_specified = len([g for g in safety_goals_data 
#                                  if g.get('safe_state') and 'to be specified' not in g.get('safe_state', '').lower()])
    
#     # FTTI specification status
#     ftti_specified = len([g for g in safety_goals_data 
#                          if g.get('ftti') and 'to be determined' not in g.get('ftti', '').lower()])
    
#     # Build statistics output
#     stats = f"""📊 **HARA Statistics: {system_name}**

# **Total Safety Goals:** {total}

# **ASIL Distribution:**
# """
    
#     for asil in ['D', 'C', 'B', 'A']:
#         if asil in asil_dist:
#             percentage = (asil_dist[asil] / total) * 100
#             bar = '█' * int(percentage / 5)
#             stats += f"- ASIL {asil}: {asil_dist[asil]:2d} ({percentage:5.1f}%) {bar}\n"
    
#     stats += f"""

# **Specification Completeness:**
# - Safe States Specified: {safe_states_specified}/{total} ({safe_states_specified*100//total if total else 0}%)
# - FTTI Specified: {ftti_specified}/{total} ({ftti_specified*100//total if total else 0}%)

# **Hazard Profile Distribution:**
# """
    
#     # Count severity levels
#     severity_dist = {}
#     for goal in safety_goals_data:
#         s = goal.get('severity', 'Unknown')
#         severity_dist[s] = severity_dist.get(s, 0) + 1
    
#     if severity_dist and 'Unknown' not in severity_dist:
#         for level in ['S3', 'S2', 'S1', 'S0']:
#             if level in severity_dist:
#                 stats += f"- {level}: {severity_dist[level]} goals\n"
    
#     stats += f"""

# **ISO 26262-3:2018 Compliance:**
# - ✅ 7.3.1: HARA prerequisites loaded
# - ✅ Safety goals with ASIL ratings available
# - {'✅' if safe_states_specified == total else '⚠️'} 7.4.2.5: Safe states {'fully specified' if safe_states_specified == total else 'partially specified'}
# - {'✅' if ftti_specified == total else '⚠️'} 7.4.2.4.b: FTTI {'fully specified' if ftti_specified == total else 'partially specified'}

# **Ready for FSC Development:** {'✅ Yes' if total > 0 else '❌ No safety goals found'}

# ---

# **Next Step:** `develop safety strategy for all goals`
# """
    
#     return stats


# # ============================================================================
# # HELPER FUNCTIONS
# # ============================================================================

# def _build_hara_summary(hara_data, validation_result):
#     """Build HARA loading summary with table format"""
    
#     # Count by ASIL
#     asil_counts = {}
#     for goal in hara_data.goals:
#         asil = goal.asil
#         asil_counts[asil] = asil_counts.get(asil, 0) + 1
    
#     summary = f"""✅ **HARA Loaded Successfully -> Safety Goals identified: (ISO 26262-3:2018, 7.3.1)**

# Source: {hara_data.source}
# Safety Goals Extracted: **{len(hara_data.goals)}**

# ASIL Distribution:
# """
    
#     for asil in ['D', 'C', 'B', 'A', 'QM']:
#         if asil in asil_counts:
#             summary += f"- **ASIL {asil}**: ({asil_counts[asil]} Safety Goal {'s' if asil_counts[asil] != 1 else ''}) "
    
#     # Add validation summary if there are warnings
#     if validation_result.has_warnings():
#         summary += f"\n⚠️ **Validation Warnings:** {len([i for i in validation_result.issues if i.severity == 'warning'])}\n"
#         summary += "*(Review with `show HARA statistics` for details)*\n"
    
#     summary += "\n---\n\n"
#     summary += "## 📋 Safety Goals Overview\n\n"
    
#     # Create markdown table
#     summary += _build_safety_goals_table(hara_data.goals)
#     summary += "\n---\n\n" 
#     return summary


# def _build_safety_goals_table(goals):
    
#     """Build markdown table for safety goals"""
    
#     # Build table header
#     table = "| SG ID | Safety Goal | ASIL | Safe State | FTTI |\n"
#     table += "|-------|-------------|------|------------|------|\n"
    
#     # Add data rows
#     for goal in goals:
#         sg_id = goal.id
#         description = goal.description
#         asil = goal.asil
#         safe_state = goal.safe_state if goal.safe_state else 'To be specified'
#         ftti = goal.ftti if goal.ftti else 'TBD'
        
#         # Truncate long descriptions
#         if len(description) > 80:
#             description = description[:77] + "..."
        
#         # Truncate long safe states
#         if len(safe_state) > 40:
#             safe_state = safe_state[:37] + "..."
        
#         # Clean FTTI for display
#         if "To be determined" in ftti:
#             ftti = "TBD"
#         elif len(ftti) > 20:
#             ftti = ftti[:17] + "..."
        
#         # Add row
#         table += f"| {sg_id} | {description} | {asil} | {safe_state} | {ftti} |\n"
    
#     return table