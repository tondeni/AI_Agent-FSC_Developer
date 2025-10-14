"""
ISO 26262 Utilities for FSC Developer Plugin
Provides ISO 26262-specific validation, mapping, and utility functions
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum


# ASIL Levels as defined in ISO 26262
class ASILLevel(str, Enum):
    """ASIL (Automotive Safety Integrity Level) classifications"""
    QM = "QM"  # Quality Management (no ASIL)
    A = "ASIL A"
    B = "ASIL B"
    C = "ASIL C"
    D = "ASIL D"


# FSR Types according to ISO 26262
class FSRType(str, Enum):
    """Functional Safety Requirement types"""
    FAULT_DETECTION = "Fault Detection"
    FAULT_HANDLING = "Fault Handling"
    ARBITRATION = "Arbitration Logic"
    DEGRADATION = "Safe Degradation"
    TRANSITION = "Transition to Safe State"
    REDUNDANCY = "Redundancy"
    MONITORING = "Monitoring"
    WARNING = "Driver Warning"
    OPERATIONAL = "Operational Requirement"


# ISO 26262 Part References
ISO_PART_3 = "ISO 26262-3"  # Concept Phase
ISO_PART_4 = "ISO 26262-4"  # Product Development: System Level
ISO_PART_5 = "ISO 26262-5"  # Product Development: Hardware Level
ISO_PART_6 = "ISO 26262-6"  # Product Development: Software Level
ISO_PART_8 = "ISO 26262-8"  # Supporting Processes
ISO_PART_9 = "ISO 26262-9"  # ASIL-oriented and safety-oriented analyses


def validate_asil(asil: str) -> Tuple[bool, str]:
    """
    Validate if an ASIL level is valid according to ISO 26262.
    
    Args:
        asil: ASIL level string to validate
        
    Returns:
        Tuple of (is_valid, normalized_asil_or_error_message)
    """
    if not asil:
        return False, "ASIL level cannot be empty"
    
    # Normalize input
    asil_upper = asil.upper().strip()
    
    # Check for valid ASIL levels
    valid_asils = {
        "QM": ASILLevel.QM,
        "A": ASILLevel.A,
        "ASIL A": ASILLevel.A,
        "ASILA": ASILLevel.A,
        "B": ASILLevel.B,
        "ASIL B": ASILLevel.B,
        "ASILB": ASILLevel.B,
        "C": ASILLevel.C,
        "ASIL C": ASILLevel.C,
        "ASILC": ASILLevel.C,
        "D": ASILLevel.D,
        "ASIL D": ASILLevel.D,
        "ASILD": ASILLevel.D,
    }
    
    if asil_upper in valid_asils:
        return True, valid_asils[asil_upper].value
    
    return False, f"Invalid ASIL level: {asil}. Valid levels are QM, ASIL A, ASIL B, ASIL C, ASIL D"


def compare_asil(asil1: str, asil2: str) -> int:
    """
    Compare two ASIL levels.
    
    Args:
        asil1: First ASIL level
        asil2: Second ASIL level
        
    Returns:
        -1 if asil1 < asil2, 0 if equal, 1 if asil1 > asil2
    """
    asil_order = {"QM": 0, "ASIL A": 1, "ASIL B": 2, "ASIL C": 3, "ASIL D": 4}
    
    # Validate and normalize
    valid1, normalized1 = validate_asil(asil1)
    valid2, normalized2 = validate_asil(asil2)
    
    if not valid1 or not valid2:
        return 0
    
    level1 = asil_order.get(normalized1, 0)
    level2 = asil_order.get(normalized2, 0)
    
    if level1 < level2:
        return -1
    elif level1 > level2:
        return 1
    else:
        return 0


def get_higher_asil(asil1: str, asil2: str) -> str:
    """
    Return the higher of two ASIL levels (ASIL decomposition rule).
    
    Args:
        asil1: First ASIL level
        asil2: Second ASIL level
        
    Returns:
        The higher ASIL level
    """
    comparison = compare_asil(asil1, asil2)
    
    if comparison >= 0:
        valid, normalized = validate_asil(asil1)
        return normalized if valid else "QM"
    else:
        valid, normalized = validate_asil(asil2)
        return normalized if valid else "QM"


def asil_decomposition_valid(parent_asil: str, child1_asil: str, child2_asil: str) -> Tuple[bool, str]:
    """
    Validate ASIL decomposition according to ISO 26262-9:2018 Clause 5.
    
    Args:
        parent_asil: Parent safety goal ASIL
        child1_asil: First decomposed element ASIL
        child2_asil: Second decomposed element ASIL
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Valid decomposition combinations (parent -> (child1, child2))
    valid_decompositions = {
        "ASIL D": [("ASIL D", "ASIL A"), ("ASIL C", "ASIL B"), ("ASIL B", "ASIL B")],
        "ASIL C": [("ASIL C", "ASIL A"), ("ASIL B", "ASIL B")],
        "ASIL B": [("ASIL B", "ASIL A")],
        "ASIL A": [],  # Cannot decompose ASIL A
        "QM": []  # Cannot decompose QM
    }
    
    # Validate inputs
    valid_parent, parent = validate_asil(parent_asil)
    valid_child1, child1 = validate_asil(child1_asil)
    valid_child2, child2 = validate_asil(child2_asil)
    
    if not all([valid_parent, valid_child1, valid_child2]):
        return False, "Invalid ASIL level in decomposition"
    
    if parent not in valid_decompositions:
        return False, f"{parent} cannot be decomposed"
    
    # Check if this decomposition is valid (order doesn't matter)
    for valid_combo in valid_decompositions[parent]:
        if (child1, child2) == valid_combo or (child2, child1) == valid_combo:
            return True, f"Valid decomposition: {parent} → {child1} + {child2}"
    
    return False, f"Invalid decomposition: {parent} cannot be decomposed to {child1} + {child2}"


def get_iso_reference_for_work_product(work_product: str) -> str:
    """
    Get the relevant ISO 26262 part and clause for a work product.
    
    Args:
        work_product: Name of the work product
        
    Returns:
        ISO 26262 reference string
    """
    references = {
        "hara": f"{ISO_PART_3} Clause 7 - Hazard analysis and risk assessment",
        "safety_goal": f"{ISO_PART_3} Clause 7.4.2 - Safety goals",
        "safety_concept": f"{ISO_PART_3} Clause 8 - Functional safety concept",
        "fsr": f"{ISO_PART_3} Clause 8.4 - Functional safety requirements",
        "item_definition": f"{ISO_PART_3} Clause 5 - Item definition",
        "technical_safety_concept": f"{ISO_PART_4} Clause 6 - Technical safety concept",
        "system_design": f"{ISO_PART_4} Clause 7 - System design",
        "hardware_requirements": f"{ISO_PART_5} Clause 6 - Hardware safety requirements",
        "software_requirements": f"{ISO_PART_6} Clause 6 - Software safety requirements",
        "verification": f"{ISO_PART_8} Clause 9 - Verification",
        "validation": f"{ISO_PART_4} Clause 8 - Validation"
    }
    
    return references.get(work_product.lower(), f"{ISO_PART_3} - ISO 26262 Concept Phase")


def validate_safety_goal_format(safety_goal: str) -> Tuple[bool, List[str]]:
    """
    Validate if a safety goal follows ISO 26262 best practices.
    
    Args:
        safety_goal: Safety goal text
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if not safety_goal or len(safety_goal.strip()) < 10:
        issues.append("Safety goal is too short or empty")
        return False, issues
    
    # Check for key elements
    goal_lower = safety_goal.lower()
    
    # Should express what NOT to happen (negative form)
    negative_indicators = ["shall not", "prevent", "avoid", "shall maintain", "ensure"]
    has_negative = any(indicator in goal_lower for indicator in negative_indicators)
    
    if not has_negative:
        issues.append("Safety goal should express what shall NOT happen or what shall be prevented")
    
    # Should be specific about the hazard
    if len(safety_goal.split()) < 8:
        issues.append("Safety goal may be too vague - consider adding more specific details")
    
    # Should start with "The system" or "The [item]"
    if not (safety_goal.strip().lower().startswith("the ")):
        issues.append("Safety goal should start with 'The system' or 'The [item name]'")
    
    # Should contain "shall"
    if "shall" not in goal_lower:
        issues.append("Safety goal should use 'shall' to express requirement")
    
    return len(issues) == 0, issues


def classify_fsr_type(fsr_description: str) -> FSRType:
    """
    Automatically classify an FSR based on its description.
    
    Args:
        fsr_description: FSR description text
        
    Returns:
        FSRType classification
    """
    desc_lower = fsr_description.lower()
    
    # Keywords for each FSR type
    classifications = {
        FSRType.FAULT_DETECTION: ["detect", "detection", "diagnose", "identify fault", "monitor for fault"],
        FSRType.FAULT_HANDLING: ["handle", "handling", "respond to fault", "fault reaction", "mitigate"],
        FSRType.ARBITRATION: ["arbitrate", "arbitration", "select", "priority", "choose between"],
        FSRType.DEGRADATION: ["degrade", "degradation", "limited functionality", "reduced performance"],
        FSRType.TRANSITION: ["transition", "switch to safe state", "enter safe state", "achieve safe state"],
        FSRType.REDUNDANCY: ["redundant", "redundancy", "backup", "fallback", "secondary"],
        FSRType.MONITORING: ["monitor", "monitoring", "supervise", "check", "verify operation"],
        FSRType.WARNING: ["warn", "warning", "alert", "notify driver", "inform"],
        FSRType.OPERATIONAL: ["operate", "operational", "normal operation", "function"]
    }
    
    # Count keyword matches
    scores = {}
    for fsr_type, keywords in classifications.items():
        score = sum(1 for keyword in keywords if keyword in desc_lower)
        if score > 0:
            scores[fsr_type] = score
    
    # Return type with highest score, default to OPERATIONAL
    if scores:
        return max(scores, key=scores.get)
    
    return FSRType.OPERATIONAL


def generate_fsr_id(safety_goal_id: str, fsr_number: int) -> str:
    """
    Generate a standardized FSR ID based on safety goal.
    
    Args:
        safety_goal_id: Safety goal identifier (e.g., "SG-01")
        fsr_number: FSR sequence number
        
    Returns:
        FSR ID string (e.g., "FSR-SG01-001")
    """
    # Clean safety goal ID
    sg_clean = safety_goal_id.replace("SG-", "").replace("SG", "").strip()
    
    # Format FSR ID
    return f"FSR-SG{sg_clean.zfill(2)}-{str(fsr_number).zfill(3)}"


def validate_safe_state_definition(safe_state: str) -> Tuple[bool, List[str]]:
    """
    Validate if a safe state definition is complete according to ISO 26262.
    
    Args:
        safe_state: Safe state description
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if not safe_state or len(safe_state.strip()) < 10:
        issues.append("Safe state description is too short or empty")
        return False, issues
    
    state_lower = safe_state.lower()
    
    # Check for key elements
    key_elements = {
        "condition": ["state", "condition", "mode"],
        "behavior": ["behave", "operate", "function", "perform"],
        "safety": ["safe", "without unreasonable risk", "prevent"]
    }
    
    for element, keywords in key_elements.items():
        if not any(keyword in state_lower for keyword in keywords):
            issues.append(f"Safe state should describe the {element} aspect")
    
    # Should be specific
    if len(safe_state.split()) < 10:
        issues.append("Safe state description may be too vague - add more specific details")
    
    return len(issues) == 0, issues


def get_verification_methods_for_asil(asil: str) -> List[str]:
    """
    Get recommended verification methods based on ASIL level.
    
    Args:
        asil: ASIL level
        
    Returns:
        List of recommended verification methods
    """
    valid, normalized_asil = validate_asil(asil)
    
    if not valid:
        return []
    
    # Base methods for all ASILs
    methods = [
        "Requirements review",
        "Design review",
        "Test specification review"
    ]
    
    # Additional methods based on ASIL
    if normalized_asil in ["ASIL B", "ASIL C", "ASIL D"]:
        methods.extend([
            "Walk-through",
            "Inspection",
            "Simulation"
        ])
    
    if normalized_asil in ["ASIL C", "ASIL D"]:
        methods.extend([
            "Formal verification",
            "Fault injection testing",
            "Back-to-back comparison"
        ])
    
    if normalized_asil == "ASIL D":
        methods.extend([
            "Proven in use argument",
            "Field monitoring"
        ])
    
    return methods


def format_iso_traceability(from_item: str, to_item: str) -> str:
    """
    Format a traceability link between ISO 26262 work products.
    
    Args:
        from_item: Source item identifier
        to_item: Target item identifier
        
    Returns:
        Formatted traceability string
    """
    return f"{from_item} → {to_item}"


def get_asil_color_code(asil: str) -> str:
    """
    Get a color code for an ASIL level (useful for visualization).
    
    Args:
        asil: ASIL level
        
    Returns:
        Hex color code string
    """
    valid, normalized = validate_asil(asil)
    
    if not valid:
        return "#CCCCCC"  # Gray for invalid
    
    colors = {
        "QM": "#90EE90",        # Light green
        "ASIL A": "#FFFF99",    # Light yellow
        "ASIL B": "#FFD700",    # Gold
        "ASIL C": "#FFA500",    # Orange
        "ASIL D": "#FF6347"     # Red
    }
    
    return colors.get(normalized, "#CCCCCC")


def estimate_development_effort(asil: str, num_fsrs: int) -> Dict[str, str]:
    """
    Estimate development effort based on ASIL and number of FSRs.
    
    Args:
        asil: ASIL level
        num_fsrs: Number of functional safety requirements
        
    Returns:
        Dictionary with effort estimates
    """
    valid, normalized = validate_asil(asil)
    
    if not valid:
        return {"error": "Invalid ASIL level"}
    
    # Complexity multipliers
    asil_multipliers = {
        "QM": 1.0,
        "ASIL A": 1.5,
        "ASIL B": 2.0,
        "ASIL C": 3.0,
        "ASIL D": 4.5
    }
    
    base_hours_per_fsr = 8  # Base hours per FSR
    multiplier = asil_multipliers.get(normalized, 1.0)
    
    total_hours = num_fsrs * base_hours_per_fsr * multiplier
    
    effort_level = "Low"
    if total_hours > 200:
        effort_level = "Medium"
    if total_hours > 500:
        effort_level = "High"
    if total_hours > 1000:
        effort_level = "Very High"
    
    return {
        "asil": normalized,
        "num_fsrs": str(num_fsrs),
        "estimated_hours": f"{total_hours:.0f}",
        "estimated_weeks": f"{total_hours / 40:.1f}",
        "effort_level": effort_level,
        "notes": f"Estimate based on {num_fsrs} FSRs at {normalized}"
    }