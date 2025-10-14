# parsers/csv_parser.py
# CSV HARA file parser

import csv
from typing import Optional, Dict, List
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from parsers.base_parser import BaseHARAParser, ParserError
from core.models import HaraData, SafetyGoal
from core.constants import HARA_COLUMN_MAPPINGS, DEFAULT_SAFE_STATE, DEFAULT_FTTI


class CSVHARAParser(BaseHARAParser):
    """Parser for CSV HARA files"""
    
    def __init__(self, file_path: str, item_name: str):
        super().__init__(item_name)
        self.file_path = file_path
    
    def can_parse(self) -> bool:
        return os.path.exists(self.file_path) and self.file_path.lower().endswith('.csv')
    
    def parse(self) -> Optional[HaraData]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                return None
            
            header_mapping = self._find_headers(rows)
            if not header_mapping or 'safety_goal' not in header_mapping:
                return None
            
            goals = self._extract_goals(rows, header_mapping)
            return self._create_hara_data(goals, f"CSV file: {os.path.basename(self.file_path)}")
            
        except Exception as e:
            raise ParserError(f"Error parsing CSV: {e}")
    
    def _find_headers(self, rows: List[List]) -> Optional[Dict]:
        """Find header row in CSV"""
        for idx, row in enumerate(rows[:10]):
            row_lower = [str(cell).lower().strip() for cell in row]
            
            # Check if this row has safety goal column
            has_goal = any(
                col_name in val 
                for val in row_lower 
                for col_name in HARA_COLUMN_MAPPINGS['safety_goal']
            )
            
            if has_goal:
                header_mapping = {'header_row': idx}
                for col_idx, val in enumerate(row_lower):
                    for field_name, possible_names in HARA_COLUMN_MAPPINGS.items():
                        if any(name in val for name in possible_names):
                            header_mapping[field_name] = col_idx
                return header_mapping
        
        return None
    
    def _extract_goals(self, rows: List[List], header_mapping: Dict) -> List[SafetyGoal]:
        """Extract safety goals from CSV rows"""
        goals = []
        header_row = header_mapping.get('header_row', 0)
        sg_counter = 1
        
        for row in rows[header_row + 1:]:
            sg_col = header_mapping['safety_goal']
            safety_goal = row[sg_col].strip() if sg_col < len(row) else ''
            
            if not safety_goal:
                continue
            
            asil_col = header_mapping.get('asil')
            asil = self._normalize_asil(row[asil_col]) if asil_col and asil_col < len(row) else 'QM'
            
            if asil == 'QM':
                continue
            
            goal = SafetyGoal(
                id=self._generate_goal_id(sg_counter),
                description=self._clean_text(safety_goal),
                asil=asil,
                safe_state=self._get_value(row, header_mapping.get('safe_state'), DEFAULT_SAFE_STATE),
                ftti=self._get_value(row, header_mapping.get('ftti'), DEFAULT_FTTI),
                severity=self._get_value(row, header_mapping.get('severity')),
                exposure=self._get_value(row, header_mapping.get('exposure')),
                controllability=self._get_value(row, header_mapping.get('controllability'))
            )
            
            goals.append(goal)
            sg_counter += 1
        
        return goals
    
    def _get_value(self, row: List, idx: Optional[int], default: str = "") -> str:
        """Safely get value from CSV row"""
        if idx is not None and idx < len(row):
            return self._clean_text(row[idx])
        return default