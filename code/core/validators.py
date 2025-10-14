# core/validators.py
# ISO 26262-3:2018 validation logic for FSC development
# Validates safety goals, strategies, FSRs, and complete FSC work products

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import (
    SafetyGoal,
    SafetyStrategy,
    FunctionalSafetyRequirement,
    ValidationCriterion,
    FSCWorkProduct
)
from core.constants import (
    SAFETY_RELEVANT_ASILS,
    MIN_FSRS_PER_GOAL,
    RECOMMENDED_FSRS_PER_GOAL,
    get_iso_reference
)


# ============================================================================
# VALIDATION RESULT CLASSES
# ============================================================================

@dataclass
class ValidationIssue:
    """
    Represents a validation issue found during checks.
    
    Attributes:
        severity: Issue severity level ('error', 'warning', 'info')
        category: Issue category (e.g., 'completeness', 'consistency', 'correctness')
        iso_clause: ISO 26262 clause reference (e.g., '7.4.2.2')
        message: Human-readable description of the issue
        item_id: Optional ID of affected item (SG-001, FSR-001, etc.)
    """
    severity: str
    category: str
    iso_clause: str
    message: str
    item_id: Optional[str] = None
    
    def __str__(self) -> str:
        """Format issue as string with emoji and details"""
        severity_emoji = {
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        emoji = severity_emoji.get(self.severity, '•')
        item_ref = f" [{self.item_id}]" if self.item_id else ""
        return f"{emoji} {self.severity.upper()}: {self.message} (ISO {self.iso_clause}){item_ref}"


@dataclass
class ValidationResult:
    """
    Result of validation checks.
    
    Attributes:
        passed: True if validation passed (no errors)
        issues: List of ValidationIssue objects found during validation
    """
    passed: bool
    issues: List[ValidationIssue]
    
    def __bool__(self) -> bool:
        """Allow boolean evaluation of result"""
        return self.passed
    
    def has_errors(self) -> bool:
        """Check if there are any error-level issues"""
        return any(issue.severity == 'error' for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues"""
        return any(issue.severity == 'warning' for issue in self.issues)
    
    def get_summary(self) -> str:
        """Get one-line summary of validation results"""
        errors = sum(1 for i in self.issues if i.severity == 'error')
        warnings = sum(1 for i in self.issues if i.severity == 'warning')
        infos = sum(1 for i in self.issues if i.severity == 'info')
        
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"{status} - Errors: {errors}, Warnings: {warnings}, Info: {infos}"
    
    def format_report(self) -> str:
        """Format full validation report with all issues"""
        report = [self.get_summary(), ""]
        
        if self.issues:
            # Group by category
            by_category = {}
            for issue in self.issues:
                if issue.category not in by_category:
                    by_category[issue.category] = []
                by_category[issue.category].append(issue)
            
            for category, issues in sorted(by_category.items()):
                report.append(f"\n### {category.upper()}")
                for issue in issues:
                    report.append(str(issue))
        else:
            report.append("No issues found.")
        
        return "\n".join(report)


# ============================================================================
# SAFETY GOAL VALIDATORS
# ============================================================================

class SafetyGoalValidator:
    """
    Validates safety goals per ISO 26262-3:2018, Clause 6.4.6.
    
    Checks:
    - Goal description is meaningful
    - ASIL level is valid
    - Safe state is specified
    - FTTI is specified for time-critical goals
    - Goal is result-oriented (not implementation-specific)
    """
    
    @staticmethod
    def validate_goal(goal: SafetyGoal) -> ValidationResult:
        """
        Validate a single safety goal.
        
        Args:
            goal: SafetyGoal to validate
            
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        
        # Check: Goal has meaningful description
        if not goal.description or len(goal.description.strip()) < 10:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='6.4.6',
                message='Safety goal description too short or missing (min 10 characters)',
                item_id=goal.id
            ))
        
        # Check: ASIL is valid
        if goal.asil not in SAFETY_RELEVANT_ASILS and goal.asil != 'QM':
            issues.append(ValidationIssue(
                severity='error',
                category='correctness',
                iso_clause='6.4.5',
                message=f'Invalid ASIL level: {goal.asil} (must be A, B, C, D, or QM)',
                item_id=goal.id
            ))
        
        # Check: Safe state specified (if not QM)
        if goal.is_safety_relevant():
            if not goal.safe_state:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='completeness',
                    iso_clause='7.4.2.5',
                    message='Safe state not specified for safety-relevant goal',
                    item_id=goal.id
                ))
            elif 'to be specified' in goal.safe_state.lower():
                issues.append(ValidationIssue(
                    severity='info',
                    category='completeness',
                    iso_clause='7.4.2.5',
                    message='Safe state is placeholder - needs specification',
                    item_id=goal.id
                ))
        
        # Check: FTTI specified for time-critical goals
        if goal.is_safety_relevant():
            if not goal.ftti:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='completeness',
                    iso_clause='7.4.2.4.b',
                    message='FTTI not specified for safety-relevant goal',
                    item_id=goal.id
                ))
            elif 'to be determined' in goal.ftti.lower():
                issues.append(ValidationIssue(
                    severity='info',
                    category='completeness',
                    iso_clause='7.4.2.4.b',
                    message='FTTI is placeholder - needs determination',
                    item_id=goal.id
                ))
        
        # Check: Goal is result-oriented (not implementation-specific)
        implementation_keywords = [
            'using', 'via', 'through', 'by means of', 'implement',
            'by using', 'utilizing', 'with the use of'
        ]
        if any(keyword in goal.description.lower() for keyword in implementation_keywords):
            issues.append(ValidationIssue(
                severity='warning',
                category='correctness',
                iso_clause='6.4.6',
                message='Safety goal appears implementation-specific rather than result-oriented',
                item_id=goal.id
            ))
        
        # Check: Goal describes "what" not "how"
        if goal.description and goal.description.lower().startswith(('design', 'implement', 'use')):
            issues.append(ValidationIssue(
                severity='info',
                category='correctness',
                iso_clause='6.4.6',
                message='Goal should describe required outcome, not implementation approach',
                item_id=goal.id
            ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )
    
    @staticmethod
    def validate_goals(goals: List[SafetyGoal]) -> ValidationResult:
        """
        Validate a list of safety goals.
        
        Args:
            goals: List of SafetyGoal objects
            
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        
        # Check: At least one safety goal exists
        if not goals:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='6.4.6',
                message='No safety goals defined - at least one required'
            ))
            return ValidationResult(passed=False, issues=issues)
        
        # Check: At least one safety-relevant goal (not all QM)
        safety_relevant = [g for g in goals if g.is_safety_relevant()]
        if not safety_relevant:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='6.4.6',
                message='No safety-relevant goals found (all are QM - no ASIL A/B/C/D)'
            ))
        
        # Validate each goal individually
        for goal in goals:
            result = SafetyGoalValidator.validate_goal(goal)
            issues.extend(result.issues)
        
        # Check: Unique IDs
        ids = [g.id for g in goals]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            issues.append(ValidationIssue(
                severity='error',
                category='correctness',
                iso_clause='General',
                message=f'Duplicate safety goal IDs found: {", ".join(set(duplicates))}'
            ))
        
        # Info: ASIL distribution
        asil_counts = {}
        for goal in safety_relevant:
            asil_counts[goal.asil] = asil_counts.get(goal.asil, 0) + 1
        
        if asil_counts:
            distribution = ", ".join([f"ASIL {k}: {v}" for k, v in sorted(asil_counts.items())])
            issues.append(ValidationIssue(
                severity='info',
                category='statistics',
                iso_clause='6.4.5',
                message=f'ASIL distribution - {distribution}'
            ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )


# ============================================================================
# STRATEGY VALIDATORS
# ============================================================================

class StrategyValidator:
    """
    Validates safety strategies per ISO 26262-3:2018, Clause 7.4.2.3.
    
    Checks:
    - All 9 required strategies are present
    - Each strategy has meaningful content
    - Strategy exists for each safety goal
    """
    
    REQUIRED_STRATEGIES = [
        'fault_avoidance',          # 7.4.2.3.a
        'fault_detection',          # 7.4.2.3.b
        'fault_control',            # 7.4.2.3.b
        'safe_state_transition',    # 7.4.2.3.c
        'fault_tolerance',          # 7.4.2.3.d
        'degradation',              # 7.4.2.3.e
        'warning_exposure',         # 7.4.2.3.f
        'warning_controllability',  # 7.4.2.3.g
        'timing',                   # 7.4.2.3.h
        'arbitration'               # 7.4.2.3.i
    ]
    
    STRATEGY_NAMES = {
        'fault_avoidance': 'Fault Avoidance (7.4.2.3.a)',
        'fault_detection': 'Fault Detection (7.4.2.3.b)',
        'fault_control': 'Fault Control (7.4.2.3.b)',
        'safe_state_transition': 'Safe State Transition (7.4.2.3.c)',
        'fault_tolerance': 'Fault Tolerance (7.4.2.3.d)',
        'degradation': 'Degradation (7.4.2.3.e)',
        'warning_exposure': 'Warning - Exposure Reduction (7.4.2.3.f)',
        'warning_controllability': 'Warning - Controllability (7.4.2.3.g)',
        'timing': 'Timing Requirements (7.4.2.3.h)',
        'arbitration': 'Arbitration (7.4.2.3.i)'
    }
    
    @staticmethod
    def validate_strategy(strategy: SafetyStrategy) -> ValidationResult:
        """
        Validate a single safety strategy.
        
        Args:
            strategy: SafetyStrategy to validate
            
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        
        # Check: All required strategies present
        for required in StrategyValidator.REQUIRED_STRATEGIES:
            if required not in strategy.strategies or not strategy.strategies[required]:
                strategy_name = StrategyValidator.STRATEGY_NAMES.get(required, required)
                issues.append(ValidationIssue(
                    severity='error',
                    category='completeness',
                    iso_clause='7.4.2.3',
                    message=f'Required strategy missing: {strategy_name}',
                    item_id=strategy.safety_goal_id
                ))
        
        # Check: Each strategy has meaningful content (>20 chars)
        for strategy_type, content in strategy.strategies.items():
            if content and len(content.strip()) < 20:
                strategy_name = StrategyValidator.STRATEGY_NAMES.get(strategy_type, strategy_type)
                issues.append(ValidationIssue(
                    severity='warning',
                    category='completeness',
                    iso_clause='7.4.2.3',
                    message=f'Strategy too brief (< 20 chars): {strategy_name}',
                    item_id=strategy.safety_goal_id
                ))
            elif content and 'not applicable' in content.lower():
                strategy_name = StrategyValidator.STRATEGY_NAMES.get(strategy_type, strategy_type)
                issues.append(ValidationIssue(
                    severity='info',
                    category='completeness',
                    iso_clause='7.4.2.3',
                    message=f'Strategy marked as not applicable: {strategy_name}',
                    item_id=strategy.safety_goal_id
                ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )
    
    @staticmethod
    def validate_strategies(strategies: List[SafetyStrategy], 
                          safety_goals: List[SafetyGoal]) -> ValidationResult:
        """
        Validate all strategies against safety goals.
        
        Args:
            strategies: List of SafetyStrategy objects
            safety_goals: List of SafetyGoal objects
            
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        
        # Check: Strategy exists for each safety-relevant goal
        strategy_sg_ids = {s.safety_goal_id for s in strategies}
        for goal in safety_goals:
            if goal.is_safety_relevant() and goal.id not in strategy_sg_ids:
                issues.append(ValidationIssue(
                    severity='error',
                    category='completeness',
                    iso_clause='7.4.2.3',
                    message='No safety strategy defined for this safety goal',
                    item_id=goal.id
                ))
        
        # Validate each strategy
        for strategy in strategies:
            result = StrategyValidator.validate_strategy(strategy)
            issues.extend(result.issues)
        
        # Check: No orphaned strategies (strategies without corresponding goal)
        goal_ids = {g.id for g in safety_goals}
        for strategy in strategies:
            if strategy.safety_goal_id not in goal_ids:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='consistency',
                    iso_clause='7.4.2.3',
                    message=f'Strategy references non-existent goal: {strategy.safety_goal_id}',
                    item_id=strategy.safety_goal_id
                ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )


# ============================================================================
# FSR VALIDATORS
# ============================================================================

class FSRValidator:
    """
    Validates FSRs per ISO 26262-3:2018, Clause 7.4.2.
    
    Checks:
    - FSR completeness and correctness
    - ASIL validity and inheritance
    - Allocation to architectural elements
    - Consideration of all required aspects (7.4.2.4)
    - Verification criteria specification
    - At least one FSR per safety goal (7.4.2.2)
    """
    
    @staticmethod
    def validate_fsr(fsr: FunctionalSafetyRequirement) -> ValidationResult:
        """
        Validate a single FSR.
        
        Args:
            fsr: FunctionalSafetyRequirement to validate
            
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        
        # Check: FSR has meaningful description
        if not fsr.description or len(fsr.description.strip()) < 10:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.4.2.1',
                message='FSR description too short or missing (min 10 characters)',
                item_id=fsr.id
            ))
        
        # Check: ASIL is valid
        if fsr.asil not in SAFETY_RELEVANT_ASILS:
            issues.append(ValidationIssue(
                severity='error',
                category='correctness',
                iso_clause='7.4.2.8.a',
                message=f'Invalid ASIL level: {fsr.asil} (must be A, B, C, or D)',
                item_id=fsr.id
            ))
        
        # Check: FSR is allocated (per 7.4.2.8)
        if not fsr.allocated_to:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.4.2.8',
                message='FSR not allocated to architectural element',
                item_id=fsr.id
            ))
        elif fsr.allocated_to.lower() in ['tbd', 'to be determined', 'unknown']:
            issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                iso_clause='7.4.2.8',
                message='FSR allocation is placeholder',
                item_id=fsr.id
            ))
        
        # Check: Operating modes specified (per 7.4.2.4.a)
        if not fsr.operating_modes:
            issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                iso_clause='7.4.2.4.a',
                message='Operating modes not specified',
                item_id=fsr.id
            ))
        
        # Check: Timing/FTTI considered (per 7.4.2.4.b)
        if not fsr.timing:
            issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                iso_clause='7.4.2.4.b',
                message='FTTI/timing constraint not specified',
                item_id=fsr.id
            ))
        elif 'tbd' in fsr.timing.lower():
            issues.append(ValidationIssue(
                severity='info',
                category='completeness',
                iso_clause='7.4.2.4.b',
                message='FTTI/timing is placeholder',
                item_id=fsr.id
            ))
        
        # Check: Safe state specified (per 7.4.2.4.c)
        if not fsr.safe_state:
            issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                iso_clause='7.4.2.4.c',
                message='Safe state not specified',
                item_id=fsr.id
            ))
        
        # Check: FSR is measurable/verifiable
        if not fsr.verification_criteria:
            issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                iso_clause='7.4.2.1',
                message='Verification criteria not specified',
                item_id=fsr.id
            ))
        
        # Check: FSR is specific (avoid vague terms)
        vague_words = ['appropriate', 'adequate', 'reasonable', 'sufficient', 'properly']
        if any(word in fsr.description.lower() for word in vague_words):
            issues.append(ValidationIssue(
                severity='info',
                category='correctness',
                iso_clause='7.4.2.1',
                message='FSR contains vague terms - ensure measurability',
                item_id=fsr.id
            ))
        
        # Check: FSR has quantitative criteria
        has_numbers = any(char.isdigit() for char in fsr.description)
        if not has_numbers and fsr.type in ['Fault Detection', 'Timing']:
            issues.append(ValidationIssue(
                severity='info',
                category='correctness',
                iso_clause='7.4.2.1',
                message='FSR lacks quantitative criteria (consider adding thresholds/timing)',
                item_id=fsr.id
            ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )
    
    @staticmethod
    def validate_fsrs(fsrs: List[FunctionalSafetyRequirement],
                     safety_goals: List[SafetyGoal]) -> ValidationResult:
        """
        Validate FSRs against safety goals per ISO 26262-3:2018.
        
        Args:
            fsrs: List of FSR objects
            safety_goals: List of SafetyGoal objects
            
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        
        # Check: At least one FSR exists
        if not fsrs:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.4.2.1',
                message='No FSRs derived - at least one FSR required per safety goal'
            ))
            return ValidationResult(passed=False, issues=issues)
        
        # Check: At least one FSR per safety goal (7.4.2.2)
        for goal in safety_goals:
            if not goal.is_safety_relevant():
                continue
            
            goal_fsrs = [f for f in fsrs if f.safety_goal_id == goal.id]
            
            if len(goal_fsrs) < MIN_FSRS_PER_GOAL:
                issues.append(ValidationIssue(
                    severity='error',
                    category='completeness',
                    iso_clause='7.4.2.2',
                    message=f'Safety goal has {len(goal_fsrs)} FSRs (minimum: {MIN_FSRS_PER_GOAL} required)',
                    item_id=goal.id
                ))
            elif len(goal_fsrs) < RECOMMENDED_FSRS_PER_GOAL[0]:
                issues.append(ValidationIssue(
                    severity='info',
                    category='completeness',
                    iso_clause='7.4.2.2',
                    message=f'Safety goal has {len(goal_fsrs)} FSRs (recommended: {RECOMMENDED_FSRS_PER_GOAL[0]}-{RECOMMENDED_FSRS_PER_GOAL[1]})',
                    item_id=goal.id
                ))
            
            # Check: ASIL inheritance (7.4.2.8.a)
            for fsr in goal_fsrs:
                if fsr.asil != goal.asil:
                    issues.append(ValidationIssue(
                        severity='warning',
                        category='consistency',
                        iso_clause='7.4.2.8.a',
                        message=f'FSR ASIL ({fsr.asil}) differs from parent goal ASIL ({goal.asil}) - justify if intentional',
                        item_id=fsr.id
                    ))
        
        # Validate each FSR individually
        for fsr in fsrs:
            result = FSRValidator.validate_fsr(fsr)
            issues.extend(result.issues)
        
        # Check: Unique FSR IDs
        fsr_ids = [f.id for f in fsrs]
        if len(fsr_ids) != len(set(fsr_ids)):
            duplicates = [id for id in fsr_ids if fsr_ids.count(id) > 1]
            issues.append(ValidationIssue(
                severity='error',
                category='correctness',
                iso_clause='General',
                message=f'Duplicate FSR IDs found: {", ".join(set(duplicates))}'
            ))
        
        # Check: All FSRs allocated
        allocated_count = sum(1 for f in fsrs if f.is_allocated())
        if allocated_count < len(fsrs):
            unallocated = len(fsrs) - allocated_count
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.4.2.8',
                message=f'{unallocated} of {len(fsrs)} FSRs not allocated to architectural elements'
            ))
        
        # Info: FSR statistics
        fsr_types = {}
        for fsr in fsrs:
            fsr_types[fsr.type] = fsr_types.get(fsr.type, 0) + 1
        
        if fsr_types:
            distribution = ", ".join([f"{k}: {v}" for k, v in sorted(fsr_types.items())])
            issues.append(ValidationIssue(
                severity='info',
                category='statistics',
                iso_clause='7.4.2.1',
                message=f'FSR distribution by type - {distribution}'
            ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )


# ============================================================================
# TRACEABILITY VALIDATORS
# ============================================================================

class TraceabilityValidator:
    """
    Validates traceability per ISO 26262-8:2018, Clause 6.
    
    Checks:
    - All FSRs trace to valid safety goals
    - No orphaned FSRs
    - All safety-relevant goals have FSRs
    - Bidirectional traceability
    """
    
    @staticmethod
    def validate_traceability(safety_goals: List[SafetyGoal],
                            fsrs: List[FunctionalSafetyRequirement]) -> ValidationResult:
        """
        Validate traceability between safety goals and FSRs.
        
        Args:
            safety_goals: List of SafetyGoal objects
            fsrs: List of FSR objects
            
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        
        # Check: All FSRs trace to a valid safety goal
        sg_ids = {g.id for g in safety_goals}
        for fsr in fsrs:
            if fsr.safety_goal_id not in sg_ids:
                issues.append(ValidationIssue(
                    severity='error',
                    category='traceability',
                    iso_clause='7.4.2.1',
                    message=f'FSR references non-existent safety goal: {fsr.safety_goal_id}',
                    item_id=fsr.id
                ))
        
        # Check: No orphaned FSRs (FSRs without parent goal)
        for fsr in fsrs:
            if not fsr.safety_goal_id:
                issues.append(ValidationIssue(
                    severity='error',
                    category='traceability',
                    iso_clause='7.4.2.1',
                    message='Orphaned FSR - no parent safety goal specified',
                    item_id=fsr.id
                ))
        
        # Check: All safety-relevant goals have FSRs (bidirectional trace)
        for goal in safety_goals:
            if not goal.is_safety_relevant():
                continue
            
            goal_fsrs = [f for f in fsrs if f.safety_goal_id == goal.id]
            if not goal_fsrs:
                issues.append(ValidationIssue(
                    severity='error',
                    category='traceability',
                    iso_clause='7.4.2.2',
                    message='Safety goal has no derived FSRs - breaks traceability',
                    item_id=goal.id
                ))
        
        # Info: Traceability statistics
        if safety_goals and fsrs:
            safety_relevant = [g for g in safety_goals if g.is_safety_relevant()]
            avg_fsrs = len(fsrs) / len(safety_relevant) if safety_relevant else 0
            issues.append(ValidationIssue(
                severity='info',
                category='statistics',
                iso_clause='Traceability',
                message=f'Traceability: {len(safety_relevant)} goals → {len(fsrs)} FSRs (avg: {avg_fsrs:.1f} FSRs/goal)'
            ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )


# ============================================================================
# FSC COMPLETENESS VALIDATOR
# ============================================================================

class FSCValidator:
    """
    Validates complete FSC work product per ISO 26262-3:2018, Clause 7.
    
    Performs comprehensive validation including:
    - Safety goals validation
    - Strategies validation
    - FSRs validation
    - Traceability validation
    - Work product completeness
    """
    
    @staticmethod
    def validate_fsc(fsc: FSCWorkProduct) -> ValidationResult:
        """
        Validate complete FSC work product.
        
        Args:
            fsc: FSCWorkProduct to validate
            
        Returns:
            ValidationResult with comprehensive validation
        """
        all_issues = []
        
        # 1. Validate safety goals
        sg_result = SafetyGoalValidator.validate_goals(fsc.safety_goals)
        all_issues.extend(sg_result.issues)
        
        # 2. Validate strategies
        strategy_result = StrategyValidator.validate_strategies(
            fsc.strategies, fsc.safety_goals
        )
        all_issues.extend(strategy_result.issues)
        
        # 3. Validate FSRs
        fsr_result = FSRValidator.validate_fsrs(fsc.fsrs, fsc.safety_goals)
        all_issues.extend(fsr_result.issues)
        
        # 4. Validate traceability
        trace_result = TraceabilityValidator.validate_traceability(
            fsc.safety_goals, fsc.fsrs
        )
        all_issues.extend(trace_result.issues)
        
        # 5. Check validation criteria exist (7.4.3)
        if not fsc.validation_criteria:
            all_issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                iso_clause='7.4.3',
                message='No safety validation criteria specified'
            ))
        
        # 6. Check verification report exists (7.4.4)
        if not fsc.verification_report:
            all_issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                iso_clause='7.4.4',
                message='No FSC verification report generated'
            ))
        
        # 7. Check work product completeness (7.5)
        if not fsc.is_complete():
            all_issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.5',
                message='FSC work product incomplete - not ready for release'
            ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in all_issues),
            issues=all_issues
        )
    
    @staticmethod
    def quick_validate(safety_goals: List[SafetyGoal],
                      strategies: List[SafetyStrategy],
                      fsrs: List[FunctionalSafetyRequirement]) -> ValidationResult:
        """
        Quick validation for in-progress FSC development.
        
        Args:
            safety_goals: List of safety goals
            strategies: List of strategies
            fsrs: List of FSRs
            
        Returns:
            ValidationResult with key issues
        """
        issues = []
        
        # Quick checks for development stage
        if not safety_goals:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.3.1',
                message='No safety goals loaded - load HARA first'
            ))
            return ValidationResult(passed=False, issues=issues)
        
        if safety_goals and not strategies:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.4.2.3',
                message='No safety strategies developed'
            ))
        
        if safety_goals and not fsrs:
            issues.append(ValidationIssue(
                severity='error',
                category='completeness',
                iso_clause='7.4.2.1',
                message='No FSRs derived from safety goals'
            ))
        
        # Check FSR allocation
        if fsrs:
            unallocated = [f for f in fsrs if not f.is_allocated()]
            if unallocated:
                issues.append(ValidationIssue(
                    severity='error',
                    category='completeness',
                    iso_clause='7.4.2.8',
                    message=f'{len(unallocated)} of {len(fsrs)} FSRs not allocated'
                ))
        
        # Check basic traceability
        if fsrs and safety_goals:
            goal_ids = {g.id for g in safety_goals}
            orphaned = [f for f in fsrs if f.safety_goal_id not in goal_ids]
            if orphaned:
                issues.append(ValidationIssue(
                    severity='error',
                    category='traceability',
                    iso_clause='7.4.2.1',
                    message=f'{len(orphaned)} FSRs reference non-existent goals'
                ))
        
        return ValidationResult(
            passed=not any(i.severity == 'error' for i in issues),
            issues=issues
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def validate_safety_goals(goals: List[SafetyGoal]) -> ValidationResult:
    """
    Convenience function to validate safety goals.
    
    Args:
        goals: List of SafetyGoal objects
        
    Returns:
        ValidationResult
    """
    return SafetyGoalValidator.validate_goals(goals)


def validate_fsrs(fsrs: List[FunctionalSafetyRequirement],
                 safety_goals: List[SafetyGoal]) -> ValidationResult:
    """
    Convenience function to validate FSRs.
    
    Args:
        fsrs: List of FSR objects
        safety_goals: List of SafetyGoal objects
        
    Returns:
        ValidationResult
    """
    return FSRValidator.validate_fsrs(fsrs, safety_goals)


def validate_fsc_completeness(safety_goals: List[SafetyGoal],
                             strategies: List[SafetyStrategy],
                             fsrs: List[FunctionalSafetyRequirement]) -> ValidationResult:
    """
    Convenience function for quick FSC validation during development.
    
    Args:
        safety_goals: List of safety goals
        strategies: List of strategies
        fsrs: List of FSRs
        
    Returns:
        ValidationResult
    """
    return FSCValidator.quick_validate(safety_goals, strategies, fsrs)