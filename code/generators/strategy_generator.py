# generators/strategy_generator.py
# Business logic for generating safety strategies per ISO 26262-3:2018, Clause 7.4.2.3

from typing import List, Dict, Optional, Callable
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import SafetyGoal, SafetyStrategy
from core.constants import STRATEGY_TYPES


class StrategyGenerator:
    """
    Generates safety strategies for safety goals per ISO 26262-3:2018, Clause 7.4.2.3.
    
    For each safety goal, generates 9 required strategies:
    a) Fault avoidance
    b) Fault detection and control
    c) Safe state transition
    d) Fault tolerance
    e) Degradation
    f) Driver warning (exposure reduction)
    g) Driver warning (controllability)
    h) Timing requirements
    i) Arbitration
    """
    
    def __init__(self, llm_function: Callable[[str], str]):
        """
        Initialize strategy generator.
        
        Args:
            llm_function: Function that takes a prompt string and returns LLM response
        """
        self.llm = llm_function
    
    def generate_strategies(self, safety_goals: List[SafetyGoal], 
                          system_name: str = "the system") -> List[SafetyStrategy]:
        """
        Generate safety strategies for all safety goals.
        
        Args:
            safety_goals: List of SafetyGoal objects
            system_name: Name of the system
            
        Returns:
            List of SafetyStrategy objects
        """
        strategies = []
        
        for goal in safety_goals:
            if not goal.is_safety_relevant():
                continue
            
            strategy = self.generate_strategy_for_goal(goal, system_name)
            if strategy:
                strategies.append(strategy)
        
        return strategies
    
    def generate_strategy_for_goal(self, goal: SafetyGoal, 
                                   system_name: str = "the system") -> Optional[SafetyStrategy]:
        """
        Generate safety strategy for a single safety goal.
        
        Args:
            goal: SafetyGoal object
            system_name: Name of the system
            
        Returns:
            SafetyStrategy object or None if generation fails
        """
        # Build prompt
        prompt = self._build_strategy_prompt(goal, system_name)
        
        # Get LLM response
        try:
            response = self.llm(prompt)
            
            # Parse strategies from response
            strategies_dict = self._parse_strategies(response)
            
            # Create SafetyStrategy object
            return SafetyStrategy(
                safety_goal_id=goal.id,
                strategies=strategies_dict
            )
            
        except Exception as e:
            print(f"Error generating strategy for {goal.id}: {e}")
            return None
    
    def _build_strategy_prompt(self, goal: SafetyGoal, system_name: str) -> str:
        """
        Build LLM prompt for strategy generation.
        
        Args:
            goal: SafetyGoal object
            system_name: Name of the system
            
        Returns:
            Prompt string
        """
        prompt = f"""You are developing Functional Safety Strategies per ISO 26262-3:2018, Clause 7.4.2.3.

**System:** {system_name}
**Safety Goal ID:** {goal.id}
**Safety Goal:** {goal.description}
**ASIL:** {goal.asil}
**Safe State:** {goal.safe_state if goal.safe_state else 'To be specified'}
**FTTI:** {goal.ftti if goal.ftti else 'To be determined'}

**Your Task:**
Develop 9 comprehensive safety strategies to achieve this safety goal. Each strategy must be specific, actionable, and technically feasible.

**ISO 26262-3:2018, Clause 7.4.2.3 Requirements:**

You must specify strategies for the following:

### a) Fault Avoidance Strategy (7.4.2.3.a)
How will faults be avoided through design, component selection, or development processes?
Examples: Using high-quality components, redundant design, proven-in-use components

### b) Fault Detection Strategy (7.4.2.3.b)
How will malfunctions be detected? What monitoring mechanisms will be used?
Examples: Plausibility checks, range monitoring, checksums, watchdogs, diagnostics

### c) Fault Control Strategy (7.4.2.3.b)
How will the system control/handle detected faults to prevent hazardous behavior?
Examples: Disable faulty function, switch to backup, limit functionality

### d) Safe State Transition Strategy (7.4.2.3.c)
How will the system transition to and maintain the safe state?
Examples: Controlled shutdown, fail-safe position, emergency stop sequence

### e) Fault Tolerance Strategy (7.4.2.3.d)
How will the system tolerate faults and continue safe operation?
Examples: Redundant channels, voting mechanisms, diverse implementations

### f) Degradation Strategy (7.4.2.3.e)
How will the system degrade functionality while maintaining safety?
Examples: Reduced performance mode, limp-home mode, limited functionality

### g) Driver Warning Strategy - Exposure Reduction (7.4.2.3.f)
How will warnings reduce exposure time to the hazard?
Examples: Early warning to allow driver intervention, indication of degraded mode

### h) Driver Warning Strategy - Controllability (7.4.2.3.g)
How will warnings increase driver controllability?
Examples: Clear indication of fault, guidance on corrective actions, acoustic/visual alerts

### i) Timing Requirements Strategy (7.4.2.3.h)
What are the fault-tolerant time interval and fault handling time requirements?
Examples: Detection within Xms, reaction within Yms, FTTI = {goal.ftti if goal.ftti else 'TBD'}

### j) Arbitration Strategy (7.4.2.3.i)
How will conflicting control requests be arbitrated? (if applicable)
Examples: Safety override logic, priority mechanisms, conflict resolution

**Output Format:**

### a) Fault Avoidance Strategy
[Detailed strategy description]

### b) Fault Detection Strategy
[Detailed strategy description]

### c) Fault Control Strategy
[Detailed strategy description]

### d) Safe State Transition Strategy
[Detailed strategy description]

### e) Fault Tolerance Strategy
[Detailed strategy description]

### f) Degradation Strategy
[Detailed strategy description]

### g) Driver Warning Strategy - Exposure Reduction
[Detailed strategy description]

### h) Driver Warning Strategy - Controllability
[Detailed strategy description]

### i) Timing Requirements Strategy
[Detailed strategy description]

### j) Arbitration Strategy
[Detailed strategy description or "Not applicable - no conflicting control requests"]

**Requirements:**
- Each strategy must be specific to this safety goal and system
- Strategies must be technically feasible and implementable
- Consider ASIL {goal.asil} requirements in strategy development
- Provide concrete examples and mechanisms
- Ensure strategies work together as a cohesive safety concept

**Now develop the complete safety strategy:**
"""
        return prompt
    
    def _parse_strategies(self, response: str) -> Dict[str, str]:
        """
        Parse strategies from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Dictionary mapping strategy type to strategy text
        """
        strategies = {}
        lines = response.split('\n')
        
        current_strategy_type = None
        current_content = []
        
        strategy_markers = {
            'a) fault avoidance': 'fault_avoidance',
            'b) fault detection': 'fault_detection',
            'c) fault control': 'fault_control',
            'd) safe state transition': 'safe_state_transition',
            'e) fault tolerance': 'fault_tolerance',
            'f) degradation': 'degradation',
            'g) driver warning strategy - exposure': 'warning_exposure',
            'h) driver warning strategy - controllability': 'warning_controllability',
            'i) timing requirements': 'timing',
            'j) arbitration': 'arbitration'
        }
        
        for line in lines:
            line_lower = line.strip().lower()
            
            # Check if this line starts a new strategy section
            matched = False
            for marker, strategy_key in strategy_markers.items():
                if line_lower.startswith('###') and marker in line_lower:
                    # Save previous strategy
                    if current_strategy_type and current_content:
                        strategies[current_strategy_type] = '\n'.join(current_content).strip()
                    
                    # Start new strategy
                    current_strategy_type = strategy_key
                    current_content = []
                    matched = True
                    break
            
            if not matched and current_strategy_type:
                # Add content to current strategy
                if line.strip() and not line.strip().startswith('###'):
                    current_content.append(line)
        
        # Save last strategy
        if current_strategy_type and current_content:
            strategies[current_strategy_type] = '\n'.join(current_content).strip()
        
        # Ensure all required strategies are present (add placeholders if missing)
        required_strategies = [
            'fault_avoidance', 'fault_detection', 'fault_control',
            'safe_state_transition', 'fault_tolerance', 'degradation',
            'warning_exposure', 'warning_controllability', 'timing', 'arbitration'
        ]
        
        for req in required_strategies:
            if req not in strategies:
                strategies[req] = 'To be specified'
        
        return strategies


class StrategyFormatter:
    """Helper class for formatting strategy output"""
    
    @staticmethod
    def format_strategy_summary(strategies: List[SafetyStrategy], 
                               safety_goals: List[SafetyGoal]) -> str:
        """
        Format strategies into a readable summary.
        
        Args:
            strategies: List of SafetyStrategy objects
            safety_goals: List of SafetyGoal objects
            
        Returns:
            Formatted summary string
        """
        if not strategies:
            return "No strategies generated."
        
        summary = f"**Safety Strategies Developed:** {len(strategies)}\n\n"
        
        for strategy in strategies:
            # Find corresponding goal
            goal = next((g for g in safety_goals if g.id == strategy.safety_goal_id), None)
            
            if not goal:
                continue
            
            summary += f"## Safety Goal: {goal.id}\n"
            summary += f"**Goal:** {goal.description}\n"
            summary += f"**ASIL:** {goal.asil}\n\n"
            
            # Add each strategy
            for strategy_type, content in strategy.strategies.items():
                strategy_name = STRATEGY_TYPES.get(strategy_type, {}).get('name', strategy_type)
                iso_clause = STRATEGY_TYPES.get(strategy_type, {}).get('iso_clause', '')
                
                summary += f"### {strategy_name} ({iso_clause})\n"
                summary += f"{content}\n\n"
            
            summary += "---\n\n"
        
        return summary
    
    @staticmethod
    def format_strategy_for_goal(strategy: SafetyStrategy, 
                                 goal: SafetyGoal) -> str:
        """
        Format a single strategy for display.
        
        Args:
            strategy: SafetyStrategy object
            goal: SafetyGoal object
            
        Returns:
            Formatted strategy string
        """
        output = f"## Safety Strategy for {goal.id}\n\n"
        output += f"**Safety Goal:** {goal.description}\n"
        output += f"**ASIL:** {goal.asil}\n"
        output += f"**Safe State:** {goal.safe_state}\n"
        output += f"**FTTI:** {goal.ftti}\n\n"
        output += "---\n\n"
        
        for strategy_type in SafetyStrategy.REQUIRED_STRATEGIES:
            strategy_name = STRATEGY_TYPES.get(strategy_type, {}).get('name', strategy_type)
            iso_clause = STRATEGY_TYPES.get(strategy_type, {}).get('iso_clause', '')
            content = strategy.strategies.get(strategy_type, 'Not specified')
            
            output += f"### {strategy_name}\n"
            output += f"*ISO 26262-3:2018, {iso_clause}*\n\n"
            output += f"{content}\n\n"
        
        return output