# parsers/text_parser.py
# Text/Markdown HARA parser

import re
import os
import sys
from typing import Optional, Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from parsers.base_parser import BaseHARAParser, ParserError
from core.models import HaraData, SafetyGoal
from core.constants import DEFAULT_SAFE_STATE, DEFAULT_FTTI


class TextHARAParser(BaseHARAParser):
    """Parser for text/markdown HARA files"""
    
    def __init__(self, file_path: str, item_name: str):
        super().__init__(item_name)
        self.file_path = file_path
    
    def can_parse(self) -> bool:
        return os.path.exists(self.file_path) and self.file_path.lower().endswith(('.txt', '.md'))
    
    def parse(self) -> Optional[HaraData]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try structured text format first
            goals = self._parse_structured_format(content)
            if not goals:
                # Try markdown table format
                goals = self._parse_table_format(content)
            
            return self._create_hara_data(goals, f"Text file: {os.path.basename(self.file_path)}")
            
        except Exception as e:
            raise ParserError(f"Error parsing text file: {e}")
    
    def _parse_structured_format(self, text: str) -> List[SafetyGoal]:
        """
        Parse LLM-generated structured format.
        
        Expected format:
        ## Safety Goal for: ...
        **Safety Goal:** ...
        **ASIL:** X
        **Safe State:** ...
        **FTTI:** ...
        """
        goals = []
        current_goal = {}
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            if line.startswith('## Safety Goal'):
                if current_goal and 'description' in current_goal:
                    goals.append(self._create_goal_from_dict(current_goal, len(goals) + 1))
                current_goal = {}
            
            if line.startswith('**Safety Goal:**'):
                current_goal['description'] = line.replace('**Safety Goal:**', '').strip()
            elif line.startswith('**ASIL:**'):
                current_goal['asil'] = line.replace('**ASIL:**', '').strip()
            elif line.startswith('**Safe State:**'):
                current_goal['safe_state'] = line.replace('**Safe State:**', '').strip()
            elif 'FTTI' in line and line.startswith('**'):
                current_goal['ftti'] = re.sub(r'\*\*.*?:\*\*', '', line).strip()
        
        if current_goal and 'description' in current_goal:
            goals.append(self._create_goal_from_dict(current_goal, len(goals) + 1))
        
        return goals
    
    def _parse_table_format(self, text: str) -> List[SafetyGoal]:
        """
        Parse markdown table format.
        
        Expected format:
        | Safety Goal | ASIL | Safe State | ...
        | ----------- | ---- | ---------- | ...
        | Goal text   | B    | State...   | ...
        """
        goals = []
        lines = text.split('\n')
        header_found = False
        header_indices = {}
        
        for line in lines:
            if '|' not in line:
                continue
            
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]
            
            if not cells:
                continue
            
            if not header_found and any('safety goal' in c.lower() for c in cells):
                header_found = True
                for idx, cell in enumerate(cells):
                    cell_lower = cell.lower()
                    if 'safety goal' in cell_lower:
                        header_indices['safety_goal'] = idx
                    elif 'asil' in cell_lower:
                        header_indices['asil'] = idx
                    elif 'safe state' in cell_lower:
                        header_indices['safe_state'] = idx
                    elif 'ftti' in cell_lower:
                        header_indices['ftti'] = idx
                continue
            
            # Skip separator lines
            if all(c.startswith('-') for c in cells):
                continue
            
            if header_found and len(cells) > 0:
                sg_idx = header_indices.get('safety_goal', 0)
                asil_idx = header_indices.get('asil', 1)
                
                safety_goal = cells[sg_idx] if sg_idx < len(cells) else ''
                asil = self._normalize_asil(cells[asil_idx]) if asil_idx < len(cells) else 'QM'
                
                if safety_goal and asil != 'QM':
                    safe_state_idx = header_indices.get('safe_state')
                    ftti_idx = header_indices.get('ftti')
                    
                    goals.append(SafetyGoal(
                        id=self._generate_goal_id(len(goals) + 1),
                        description=self._clean_text(safety_goal),
                        asil=asil,
                        safe_state=cells[safe_state_idx] if safe_state_idx and safe_state_idx < len(cells) else DEFAULT_SAFE_STATE,
                        ftti=cells[ftti_idx] if ftti_idx and ftti_idx < len(cells) else DEFAULT_FTTI
                    ))
        
        return goals
    
    def _create_goal_from_dict(self, goal_dict: Dict, index: int) -> SafetyGoal:
        """Create SafetyGoal from dictionary"""
        return SafetyGoal(
            id=self._generate_goal_id(index),
            description=self._clean_text(goal_dict.get('description', '')),
            asil=self._normalize_asil(goal_dict.get('asil', 'QM')),
            safe_state=goal_dict.get('safe_state', DEFAULT_SAFE_STATE),
            ftti=goal_dict.get('ftti', DEFAULT_FTTI)
        )