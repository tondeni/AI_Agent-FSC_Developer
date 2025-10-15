# ==============================================================================
# agent_prompt_hook.py
# Add FSC context to agent prompt for intelligent formatting
# Place in: AI_Agent-FSC_Developer/agent_prompt_hook.py (root level)
# ==============================================================================

from cat.mad_hatter.decorators import hook
from cat.log import log

@hook(priority=0)
def agent_prompt_suffix(suffix, cat):
    """
    Add FSC Developer context and formatting guidelines to agent prompt.
    
    This hook:
    1. Checks what FSC data is in working memory
    2. Shows agent what data is available
    3. Provides formatting guidelines
    4. Helps agent format responses naturally
    """
    
    # Check what FSC data exists
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    strategies = cat.working_memory.get("fsc_strategies", [])
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    allocation_data = cat.working_memory.get("fsc_allocation", {})
    validation_criteria = cat.working_memory.get("fsc_validation_criteria", [])
    system_name = cat.working_memory.get("system_name", "")
    
    # If no FSC context, don't add instructions
    if not any([safety_goals, strategies, fsrs, allocation_data, validation_criteria]):
        return suffix
    
    # Build FSC context for agent
    fsc_context = """

# 🔒 ISO 26262 Functional Safety Concept Context

You are assisting with ISO 26262 Functional Safety Concept development.
"""
    
    # Add system name if available
    if system_name:
        fsc_context += f"\n**Current System**: {system_name}\n"
    
    fsc_context += "\n## Available Data in Working Memory\n\n"
    
    # Show safety goals
    if safety_goals:
        fsc_context += f"### Safety Goals ({len(safety_goals)} loaded)\n\n"
        fsc_context += "```\n"
        for goal in safety_goals[:5]:  # Show first 5
            fsc_context += f"{goal['id']} (ASIL {goal['asil']}): {goal['description'][:60]}...\n"
        if len(safety_goals) > 5:
            fsc_context += f"... and {len(safety_goals) - 5} more safety goals\n"
        fsc_context += "```\n\n"
    
    # Show strategies
    if strategies:
        fsc_context += f"### Safety Strategies ({len(strategies)} developed)\n\n"
        fsc_context += "```\n"
        for strategy in strategies[:3]:
            fsc_context += f"{strategy['safety_goal_id']}: {len(strategy.get('strategies', {}))} strategy types defined\n"
        if len(strategies) > 3:
            fsc_context += f"... and {len(strategies) - 3} more strategies\n"
        fsc_context += "```\n\n"
    
    # Show FSRs
    if fsrs:
        fsc_context += f"### Functional Safety Requirements ({len(fsrs)} derived)\n\n"
        fsc_context += "```\n"
        
        # Group by type for summary
        by_type = {}
        by_asil = {}
        for fsr in fsrs:
            fsr_type = fsr.get('type', 'Unknown')
            asil = fsr.get('asil', 'QM')
            by_type[fsr_type] = by_type.get(fsr_type, 0) + 1
            by_asil[asil] = by_asil.get(asil, 0) + 1
        
        fsc_context += "Distribution by Type:\n"
        for fsr_type, count in sorted(by_type.items()):
            fsc_context += f"  - {fsr_type}: {count} FSRs\n"
        
        fsc_context += "\nDistribution by ASIL:\n"
        for asil in ['D', 'C', 'B', 'A', 'QM']:
            if asil in by_asil:
                fsc_context += f"  - ASIL {asil}: {by_asil[asil]} FSRs\n"
        
        fsc_context += "\nSample FSRs:\n"
        for fsr in fsrs[:3]:
            fsc_context += f"  - {fsr['id']} ({fsr.get('type', 'N/A')}, ASIL {fsr.get('asil', 'QM')})\n"
        
        if len(fsrs) > 3:
            fsc_context += f"  ... and {len(fsrs) - 3} more FSRs\n"
        
        fsc_context += "```\n\n"
    
    # Show allocation status
    if allocation_data or (fsrs and any(f.get('allocated_to') for f in fsrs)):
        allocated_count = sum(1 for f in fsrs if f.get('allocated_to'))
        fsc_context += f"### Allocation Status\n\n"
        fsc_context += f"- Allocated: {allocated_count}/{len(fsrs)} FSRs\n\n"
    
    # Show validation criteria
    if validation_criteria:
        fsc_context += f"### Validation Criteria ({len(validation_criteria)} specified)\n\n"
    
    # Add formatting guidelines
    fsc_context += """## Response Formatting Guidelines

**CRITICAL: Always use actual data from working memory above. Never make up FSR IDs or content.**

### When Discussing FSRs:

Format FSR information in clear tables:

| FSR ID | Type | ASIL | Description |
|--------|------|------|-------------|
| FSR-SG-001-DET-1 | Detection | D | System shall detect battery voltage deviation... |
| FSR-SG-001-CTR-1 | Control | D | System shall transition to safe state... |

Include:
- FSR ID (exact from working memory)
- Type (Detection, Control, Warning, etc.)
- ASIL level
- Clear description
- Traceability to parent safety goal when relevant

### When Discussing Safety Goals:

| Goal ID | ASIL | Description | Safe State |
|---------|------|-------------|------------|
| SG-001 | D | Prevent battery fire | Disconnect battery |

### When Discussing Allocation:

Show allocation matrix:

| Component | FSRs Allocated | ASIL Levels |
|-----------|----------------|-------------|
| Battery Monitor | 8 FSRs | D, C |
| Safety Controller | 12 FSRs | D, D, C |

### General Formatting Rules:

1. **Use markdown tables** for multiple items (FSRs, goals, strategies)
2. **Use bold** for important terms (ASIL levels, component names)
3. **Use headers** (##, ###) to structure complex responses
4. **Use bullet lists** for steps, recommendations, or options
5. **Keep descriptions concise** (60-80 chars in tables)

### Example Good Response:

❌ BAD:
"I created some FSRs for you. They are detection and control requirements."

✅ GOOD:
"Derived 12 Functional Safety Requirements from 3 safety goals:

## FSR Summary

| FSR ID | Type | ASIL | Description |
|--------|------|------|-------------|
| FSR-SG-001-DET-1 | Detection | D | Detect battery voltage deviation within 100ms |
| FSR-SG-001-CTR-1 | Control | D | Transition to safe state upon fault detection |
| FSR-SG-001-WRN-1 | Warning | D | Alert driver of battery malfunction |

**Distribution:**
- Detection: 4 FSRs
- Control: 4 FSRs
- Warning: 2 FSRs
- Emergency Operation: 2 FSRs

All FSRs trace to their parent safety goals and include ASIL ratings per ISO 26262-3:2018."

### ISO 26262 References:

When relevant, reference ISO clauses:
- FSR specification: ISO 26262-3:2018, Clause 7.4.2
- Safety goals: ISO 26262-3:2018, Clause 6.4.6
- Allocation: ISO 26262-3:2018, Clause 7.4.2.8

### Working Memory Integration:

If suggesting next steps, check working memory status:
- If FSRs exist but not allocated → Suggest: "allocate all FSRs"
- If allocated but not validated → Suggest: "specify validation criteria"
- If everything complete → Suggest: "verify FSC" or file generation

### Important Notes:

1. **Never invent FSR IDs** - only reference FSRs that exist in working memory
2. **Always check ASIL levels** from actual data, don't assume
3. **Provide context** - explain WHY something is important per ISO 26262
4. **Be specific** - use actual numbers, counts, IDs from working memory
5. **Stay professional** - this is safety-critical automotive work

---

**Remember**: You are assisting with safety-critical systems development. Accuracy and traceability are paramount. Always reference actual data from working memory.
"""
    
    log.info("✅ Added FSC context to agent prompt")
    
    return suffix + fsc_context