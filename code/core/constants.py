# core/constants.py
# Constants and mappings for ISO 26262 FSC Development

from enum import Enum
from typing import Dict, List


# ============================================================================
# ASIL LEVELS
# ============================================================================

class ASILLevel(str, Enum):
    """ASIL (Automotive Safety Integrity Level) classifications per ISO 26262"""
    QM = "QM"      # Quality Management (no ASIL)
    A = "A"        # ASIL A
    B = "B"        # ASIL B
    C = "C"        # ASIL C
    D = "D"        # ASIL D


# Safety-relevant ASIL levels (excludes QM)
SAFETY_RELEVANT_ASILS = ["A", "B", "C", "D"]


# ============================================================================
# FSR TYPES
# ============================================================================

class FSRType(str, Enum):
    """Functional Safety Requirement types per ISO 26262-3:2018"""
    FAULT_DETECTION = "Fault Detection"
    FAULT_HANDLING = "Fault Handling"
    ARBITRATION = "Arbitration Logic"
    DEGRADATION = "Safe Degradation"
    TRANSITION = "Transition to Safe State"
    REDUNDANCY = "Redundancy"
    MONITORING = "Monitoring"
    WARNING = "Driver Warning"
    OPERATIONAL = "Operational Requirement"


# ============================================================================
# ALLOCATION TYPES
# ============================================================================

class AllocationType(str, Enum):
    """FSR allocation to architectural elements"""
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    MECHANICAL = "Mechanical"
    HYDRAULIC = "Hydraulic"
    ELECTRICAL = "Electrical"
    ELECTRONIC = "Electronic"
    SYSTEM = "System Level"
    EXTERNAL = "External Element"


# ============================================================================
# FSR TYPE CODES
# ============================================================================

# Short codes for FSR types (used in FSR IDs)
FSR_TYPE_CODES: Dict[FSRType, str] = {
    FSRType.FAULT_DETECTION: "FD",
    FSRType.FAULT_HANDLING: "FH",
    FSRType.ARBITRATION: "AR",
    FSRType.DEGRADATION: "DG",
    FSRType.TRANSITION: "TS",
    FSRType.REDUNDANCY: "RD",
    FSRType.MONITORING: "MN",
    FSRType.WARNING: "WN",
    FSRType.OPERATIONAL: "OP"
}


# ============================================================================
# HARA COLUMN MAPPINGS
# ============================================================================

# Map field names to possible column header variations
HARA_COLUMN_MAPPINGS: Dict[str, List[str]] = {
    'safety_goal': [
        'safety goal',
        'safety goals',
        'goal',
        'sg',
        'functional safety goal'
    ],
    'asil': [
        'asil',
        'asil level',
        'safety level',
        'integrity level'
    ],
    'safe_state': [
        'safe state',
        'safestate',
        'safety state',
        'ss'
    ],
    'ftti': [
        'ftti',
        'fault tolerant time interval',
        'fault tolerant time',
        'time interval',
        'reaction time'
    ],
    'severity': [
        's',
        'severity',
        'sev',
        'severity (s)'
    ],
    'exposure': [
        'e',
        'exposure',
        'exp',
        'exposure (e)'
    ],
    'controllability': [
        'c',
        'controllability',
        'ctrl',
        'control',
        'controllability (c)'
    ],
    'hazard_id': [
        'hazard id',
        'id',
        'hazard-id',
        'haz id',
        'h-id',
        'hazard number'
    ],
    'hazardous_event': [
        'hazardous event',
        'hazard event',
        'hazard',
        'he',
        'event'
    ],
    'operational_situation': [
        'operational situation',
        'operation',
        'operating situation',
        'driving situation',
        'scenario'
    ]
}


# ============================================================================
# SHEET NAME PRIORITIES
# ============================================================================

# Priority order for selecting worksheets in Excel files
HARA_SHEET_PRIORITY: List[str] = [
    'hara table',
    'hara',
    'hazard analysis',
    'hazard analysis and risk assessment',
    'safety goals',
    'fsc',
    'functional safety concept',
    'safety analysis',
    'risk assessment'
]


# ============================================================================
# DEFAULT VALUES
# ============================================================================

DEFAULT_SAFE_STATE = "System enters fail-safe mode with controlled degradation"
DEFAULT_FTTI = "To be determined based on hazard analysis"

# Default operating modes per ISO 26262-3:2018, Clause 7.4.2.4.a
DEFAULT_OPERATING_MODES = "Normal operation, Degraded operation, Emergency operation, Off"


# ============================================================================
# ISO 26262 REFERENCES
# ============================================================================

# ISO 26262 Part References
ISO_PART_3 = "ISO 26262-3:2018"  # Concept Phase
ISO_PART_4 = "ISO 26262-4:2018"  # Product Development: System Level
ISO_PART_5 = "ISO 26262-5:2018"  # Product Development: Hardware Level
ISO_PART_6 = "ISO 26262-6:2018"  # Product Development: Software Level
ISO_PART_8 = "ISO 26262-8:2018"  # Supporting Processes
ISO_PART_9 = "ISO 26262-9:2018"  # ASIL-oriented and safety-oriented analyses

# Work product references
ISO_REFERENCES: Dict[str, str] = {
    "hara": f"{ISO_PART_3} Clause 7 - Hazard analysis and risk assessment",
    "safety_goal": f"{ISO_PART_3} Clause 7.4.2 - Safety goals",
    "functional_safety_concept": f"{ISO_PART_3} Clause 8 - Functional safety concept",
    "fsr": f"{ISO_PART_3} Clause 8.4 - Functional safety requirements",
    "item_definition": f"{ISO_PART_3} Clause 5 - Item definition",
    "technical_safety_concept": f"{ISO_PART_4} Clause 6 - Technical safety concept",
    "system_design": f"{ISO_PART_4} Clause 7 - System design",
    "hardware_requirements": f"{ISO_PART_5} Clause 6 - Hardware safety requirements",
    "software_requirements": f"{ISO_PART_6} Clause 6 - Software safety requirements",
    "verification": f"{ISO_PART_8} Clause 9 - Verification",
    "validation": f"{ISO_PART_4} Clause 8 - Validation"
}


# ============================================================================
# FSR GENERATION STRATEGIES
# ============================================================================

# Strategy types per ISO 26262-3:2018, Clause 7.4.2.3
STRATEGY_TYPES: Dict[str, Dict[str, str]] = {
    'fault_avoidance': {
        'name': 'Fault Avoidance Strategy',
        'iso_clause': '7.4.2.3.a',
        'description': 'Avoid faults through design, component selection, or development processes'
    },
    'fault_detection': {
        'name': 'Fault Detection Strategy',
        'iso_clause': '7.4.2.3.b',
        'description': 'Detect malfunctions through monitoring mechanisms'
    },
    'fault_control': {
        'name': 'Fault Control Strategy',
        'iso_clause': '7.4.2.3.b',
        'description': 'Control/handle detected faults to prevent hazardous behavior'
    },
    'safe_state_transition': {
        'name': 'Safe State Transition Strategy',
        'iso_clause': '7.4.2.3.c',
        'description': 'Transition to and maintain the safe state'
    },
    'fault_tolerance': {
        'name': 'Fault Tolerance Strategy',
        'iso_clause': '7.4.2.3.d',
        'description': 'Tolerate faults and continue safe operation'
    },
    'degradation': {
        'name': 'Degradation Strategy',
        'iso_clause': '7.4.2.3.e',
        'description': 'Degrade functionality while maintaining safety'
    },
    'warning_exposure': {
        'name': 'Driver Warning Strategy - Exposure Reduction',
        'iso_clause': '7.4.2.3.f',
        'description': 'Reduce exposure time to hazard through warnings'
    },
    'warning_controllability': {
        'name': 'Driver Warning Strategy - Controllability',
        'iso_clause': '7.4.2.3.g',
        'description': 'Increase driver controllability through warnings'
    },
    'timing': {
        'name': 'Timing Requirements Strategy',
        'iso_clause': '7.4.2.3.h',
        'description': 'Define fault-tolerant time interval and fault handling time requirements'
    },
    'arbitration': {
        'name': 'Arbitration Strategy',
        'iso_clause': '7.4.2.3.i',
        'description': 'Arbitrate conflicting control requests'
    }
}

# Strategy templates for different ASIL levels
FSR_STRATEGY_TEMPLATES: Dict[str, List[str]] = {
    "A": [
        "Detection and fault handling",
        "Transition to safe state"
    ],
    "B": [
        "Detection and fault handling",
        "Transition to safe state",
        "Monitoring"
    ],
    "C": [
        "Detection and fault handling",
        "Arbitration between redundant elements",
        "Transition to safe state",
        "Monitoring",
        "Warning"
    ],
    "D": [
        "Detection and fault handling",
        "Arbitration between redundant elements", 
        "Safe degradation",
        "Transition to safe state",
        "Redundancy",
        "Monitoring",
        "Warning"
    ]
}


# ============================================================================
# VALIDATION CRITERIA
# ============================================================================

# Minimum number of FSRs required per safety goal (absolute minimum)
MIN_FSRS_PER_GOAL = 1

# Recommended number of FSRs by ASIL level
MIN_FSRS_BY_ASIL: Dict[str, int] = {
    "A": 2,
    "B": 3,
    "C": 4,
    "D": 5
}

# Recommended range of FSRs per safety goal (general guidance)
RECOMMENDED_FSRS_PER_GOAL = (3, 7)  # (min_recommended, max_recommended)


# ============================================================================
# VERIFICATION METHODS BY ASIL
# ============================================================================

VERIFICATION_METHODS: Dict[str, List[str]] = {
    "QM": [
        "Requirements review",
        "Design review"
    ],
    "A": [
        "Requirements review",
        "Design review",
        "Test specification review",
        "Walk-through"
    ],
    "B": [
        "Requirements review",
        "Design review",
        "Test specification review",
        "Walk-through",
        "Inspection",
        "Simulation"
    ],
    "C": [
        "Requirements review",
        "Design review",
        "Test specification review",
        "Walk-through",
        "Inspection",
        "Simulation",
        "Formal verification",
        "Fault injection testing"
    ],
    "D": [
        "Requirements review",
        "Design review",
        "Test specification review",
        "Walk-through",
        "Inspection",
        "Simulation",
        "Formal verification",
        "Fault injection testing",
        "Back-to-back comparison",
        "Proven in use argument"
    ]
}


# ============================================================================
# COLOR CODES FOR VISUALIZATION
# ============================================================================

ASIL_COLORS: Dict[str, str] = {
    "QM": "#90EE90",     # Light green
    "A": "#FFFF99",      # Light yellow
    "B": "#FFD700",      # Gold
    "C": "#FFA500",      # Orange
    "D": "#FF6347"       # Red (Tomato)
}


# ============================================================================
# FILE PATTERNS
# ============================================================================

# File naming patterns for HARA files
HARA_FILE_PATTERNS: List[str] = [
    '*hara*.xlsx',
    '*hara*.xls',
    '*hara*.csv',
    '*hazard*.xlsx',
    '*hazard*.xls',
    '*safety_goals*.xlsx',
    '*safety_goals*.xls'
]


# ============================================================================
# WORKFLOW STEPS
# ============================================================================

FSC_WORKFLOW_STEPS: List[Dict[str, str]] = [
    {
        "step": "1",
        "name": "Load HARA",
        "description": "Load and validate HARA data containing safety goals",
        "iso_reference": ISO_PART_3 + " Clause 7"
    },
    {
        "step": "2",
        "name": "Develop Safety Strategy",
        "description": "Define safety strategies for each safety goal",
        "iso_reference": ISO_PART_3 + " Clause 8.3"
    },
    {
        "step": "3",
        "name": "Derive FSRs",
        "description": "Derive functional safety requirements from strategies",
        "iso_reference": ISO_PART_3 + " Clause 8.4"
    },
    {
        "step": "4",
        "name": "Allocate FSRs",
        "description": "Allocate FSRs to architectural elements",
        "iso_reference": ISO_PART_3 + " Clause 8.4.5"
    },
    {
        "step": "5",
        "name": "Define Verification",
        "description": "Define verification and validation criteria",
        "iso_reference": ISO_PART_4 + " Clause 8"
    },
    {
        "step": "6",
        "name": "Generate FSC Document",
        "description": "Generate complete Functional Safety Concept document",
        "iso_reference": ISO_PART_3 + " Clause 8"
    }
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_iso_reference(work_product: str) -> str:
    """
    Get the ISO 26262 reference for a specific work product.
    
    Args:
        work_product: Name of the work product (e.g., 'hara', 'fsr', 'safety_goal')
        
    Returns:
        ISO 26262 reference string
        
    Example:
        >>> get_iso_reference('hara')
        'ISO 26262-3:2018 Clause 7 - Hazard analysis and risk assessment'
    """
    work_product_lower = work_product.lower().replace(" ", "_")
    return ISO_REFERENCES.get(work_product_lower, f"{ISO_PART_3} - ISO 26262 Concept Phase")