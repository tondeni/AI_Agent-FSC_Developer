# core/models.py
# Data models for FSC Developer Plugin
# Defines core data structures used throughout the plugin

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class SafetyGoal:
    """
    Safety Goal extracted from HARA.
    Per ISO 26262-3:2018, Clause 6.4.6
    """
    id: str
    description: str
    asil: str
    safe_state: str = ""
    ftti: str = ""
    severity: str = ""
    exposure: str = ""
    controllability: str = ""
    hazard_id: str = ""
    hazardous_event: str = ""
    operational_situation: str = ""
    
    def is_safety_relevant(self) -> bool:
        """Check if goal is safety-relevant (not QM)"""
        return self.asil.upper() in ['A', 'B', 'C', 'D']
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'description': self.description,
            'asil': self.asil,
            'safe_state': self.safe_state,
            'ftti': self.ftti,
            'severity': self.severity,
            'exposure': self.exposure,
            'controllability': self.controllability,
            'hazard_id': self.hazard_id,
            'hazardous_event': self.hazardous_event,
            'operational_situation': self.operational_situation
        }


@dataclass
class SafetyStrategy:
    """
    Safety Strategy for achieving a Safety Goal.
    Per ISO 26262-3:2018, Clause 7.4.2.3
    """
    safety_goal_id: str
    strategies: Dict[str, str] = field(default_factory=dict)
    
    # 9 required strategy types per ISO 26262-3:2018, 7.4.2.3
    REQUIRED_STRATEGIES = [
        'fault_avoidance',       # 7.4.2.3.a
        'fault_detection',       # 7.4.2.3.b
        'fault_control',         # 7.4.2.3.b
        'safe_state_transition', # 7.4.2.3.c
        'fault_tolerance',       # 7.4.2.3.d
        'degradation',           # 7.4.2.3.e
        'warning_exposure',      # 7.4.2.3.f
        'warning_controllability', # 7.4.2.3.g
        'timing',                # 7.4.2.3.h
        'arbitration'            # 7.4.2.3.i
    ]
    
    def is_complete(self) -> bool:
        """Check if all required strategies are defined"""
        return all(s in self.strategies for s in self.REQUIRED_STRATEGIES)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'safety_goal_id': self.safety_goal_id,
            'strategies': self.strategies,
            'complete': self.is_complete()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SafetyStrategy':
        """Create SafetyStrategy from dictionary (ignoring computed fields)"""
        return cls(
            safety_goal_id=data['safety_goal_id'],
            strategies=data.get('strategies', {})
        )


@dataclass
class FunctionalSafetyRequirement:
    """
    Functional Safety Requirement (FSR).
    Per ISO 26262-3:2018, Clause 7.4.2
    """
    id: str
    safety_goal_id: str
    safety_goal: str
    description: str
    asil: str
    type: str  # FSR category
    
    # Additional attributes per 7.4.2.4
    operating_modes: str = "All modes"
    timing: str = ""  # FTTI
    safe_state: str = ""
    emergency_operation: str = ""
    functional_redundancy: str = ""
    
    # Allocation per 7.4.2.8
    allocated_to: str = ""
    allocation_type: str = ""
    allocation_rationale: str = ""
    interface: str = ""
    
    # Verification
    verification_criteria: str = ""
    
    def is_allocated(self) -> bool:
        """Check if FSR is allocated to architectural element"""
        return bool(self.allocated_to)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'safety_goal_id': self.safety_goal_id,
            'safety_goal': self.safety_goal,
            'description': self.description,
            'asil': self.asil,
            'type': self.type,
            'operating_modes': self.operating_modes,
            'timing': self.timing,
            'safe_state': self.safe_state,
            'emergency_operation': self.emergency_operation,
            'functional_redundancy': self.functional_redundancy,
            'allocated_to': self.allocated_to,
            'allocation_type': self.allocation_type,
            'allocation_rationale': self.allocation_rationale,
            'interface': self.interface,
            'verification_criteria': self.verification_criteria
        }


@dataclass
class SafetyMechanism:
    """
    Safety Mechanism for implementing FSRs.
    Per ISO 26262-4:2018, Clause 6.4.5.4
    
    Safety mechanisms are technical solutions that detect, control, or tolerate faults.
    """
    id: str
    name: str
    mechanism_type: str  # diagnostic, redundancy, safe_state, supervision, communication
    description: str
    applicable_fsrs: List[str] = field(default_factory=list)
    asil_suitability: List[str] = field(default_factory=list)  # ['A', 'B', 'C', 'D']
    diagnostic_coverage: str = ""  # e.g., "90-95%", "High", "Medium"
    implementation_notes: str = ""
    verification_method: str = ""
    
    # Detailed characteristics
    detection_capability: str = ""  # For diagnostic mechanisms
    reaction_time: str = ""  # For safe state mechanisms
    independence_level: str = ""  # For redundancy mechanisms
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'mechanism_type': self.mechanism_type,
            'description': self.description,
            'applicable_fsrs': self.applicable_fsrs,
            'asil_suitability': self.asil_suitability,
            'diagnostic_coverage': self.diagnostic_coverage,
            'implementation_notes': self.implementation_notes,
            'verification_method': self.verification_method,
            'detection_capability': self.detection_capability,
            'reaction_time': self.reaction_time,
            'independence_level': self.independence_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SafetyMechanism':
        """Create SafetyMechanism from dictionary"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            mechanism_type=data.get('mechanism_type', ''),
            description=data.get('description', ''),
            applicable_fsrs=data.get('applicable_fsrs', []),
            asil_suitability=data.get('asil_suitability', []),
            diagnostic_coverage=data.get('diagnostic_coverage', ''),
            implementation_notes=data.get('implementation_notes', ''),
            verification_method=data.get('verification_method', ''),
            detection_capability=data.get('detection_capability', ''),
            reaction_time=data.get('reaction_time', ''),
            independence_level=data.get('independence_level', '')
        )
    
    def is_suitable_for_asil(self, asil: str) -> bool:
        """Check if mechanism is suitable for given ASIL level"""
        asil_clean = asil.replace('ASIL ', '').strip().upper()
        return asil_clean in [a.upper() for a in self.asil_suitability]
    
    def get_mechanism_category(self) -> str:
        """Get user-friendly mechanism category"""
        category_map = {
            'diagnostic': 'Diagnostic & Detection',
            'redundancy': 'Redundancy & Fault Tolerance',
            'safe_state': 'Safe State Management',
            'supervision': 'Supervision & Monitoring',
            'communication': 'Communication Protection'
        }
        return category_map.get(self.mechanism_type, self.mechanism_type)


@dataclass
class MechanismFSRMapping:
    """
    Mapping between safety mechanisms and FSRs.
    Tracks which mechanisms implement which requirements.
    """
    fsr_id: str
    mechanism_ids: List[str] = field(default_factory=list)
    coverage_rationale: str = ""
    residual_risk: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'fsr_id': self.fsr_id,
            'mechanism_ids': self.mechanism_ids,
            'coverage_rationale': self.coverage_rationale,
            'residual_risk': self.residual_risk
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MechanismFSRMapping':
        """Create from dictionary"""
        return cls(
            fsr_id=data.get('fsr_id', ''),
            mechanism_ids=data.get('mechanism_ids', []),
            coverage_rationale=data.get('coverage_rationale', ''),
            residual_risk=data.get('residual_risk', '')
        )


@dataclass
class ValidationCriterion:
    """
    Safety Validation Criterion.
    Per ISO 26262-3:2018, Clause 7.4.3
    """
    id: str
    fsr_id: str
    safety_goal_id: str
    criterion: str
    validation_method: str
    test_conditions: str = ""
    success_criteria: str = ""
    evidence_required: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'fsr_id': self.fsr_id,
            'safety_goal_id': self.safety_goal_id,
            'criterion': self.criterion,
            'validation_method': self.validation_method,
            'test_conditions': self.test_conditions,
            'success_criteria': self.success_criteria,
            'evidence_required': self.evidence_required
        }


@dataclass
class HaraData:
    """
    Container for HARA data loaded from various sources.
    """
    system: str
    goals: List[SafetyGoal]
    source: str = ""  # Where data came from
    
    def get_asil_distribution(self) -> Dict[str, int]:
        """Get count of goals by ASIL level"""
        distribution = {}
        for goal in self.goals:
            asil = goal.asil
            distribution[asil] = distribution.get(asil, 0) + 1
        return distribution
    
    def get_safety_relevant_goals(self) -> List[SafetyGoal]:
        """Get only safety-relevant goals (not QM)"""
        return [g for g in self.goals if g.is_safety_relevant()]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'system': self.system,
            'goals': [g.to_dict() for g in self.goals],
            'source': self.source,
            'asil_distribution': self.get_asil_distribution()
        }

@dataclass
class FSCWorkProduct:
    """
    Complete FSC Work Product.
    Per ISO 26262-3:2018, Clause 7.5
    """
    system_name: str
    safety_goals: List[SafetyGoal]
    strategies: List[SafetyStrategy]
    fsrs: List[FunctionalSafetyRequirement]
    validation_criteria: List[ValidationCriterion]
    verification_report: str = ""
    safety_mechanisms: List[SafetyMechanism] = field(default_factory=list)
    mechanism_fsr_mappings: List[MechanismFSRMapping] = field(default_factory=list)
    
    def is_complete(self) -> bool:
        """Check if FSC is complete"""
        return (
            len(self.safety_goals) > 0 and
            len(self.strategies) > 0 and
            len(self.fsrs) > 0 and
            all(fsr.is_allocated() for fsr in self.fsrs)
        )
    
    def get_statistics(self) -> Dict:
        """Get FSC statistics"""
        return {
            'system': self.system_name,
            'total_safety_goals': len(self.safety_goals),
            'total_strategies': len(self.strategies),
            'total_fsrs': len(self.fsrs),
            'allocated_fsrs': sum(1 for fsr in self.fsrs if fsr.is_allocated()),
            'validation_criteria': len(self.validation_criteria),
            'complete': self.is_complete()
        }
    