# parsers/base_parser.py
# Abstract base parser for HARA data sources

from abc import ABC, abstractmethod
from typing import Optional, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import HaraData, SafetyGoal


class BaseHARAParser(ABC):
    """
    Abstract base class for HARA parsers.
    All parser implementations must inherit from this class.
    """
    
    def __init__(self, item_name: str):
        """
        Initialize parser.
        
        Args:
            item_name: Name of the item/system
        """
        self.item_name = item_name
    
    @abstractmethod
    def parse(self) -> Optional[HaraData]:
        """
        Parse HARA data from source.
        
        Returns:
            HaraData object if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def can_parse(self) -> bool:
        """
        Check if this parser can handle the data source.
        
        Returns:
            True if parser can handle the source, False otherwise
        """
        pass
    
    def _create_hara_data(self, goals: List[SafetyGoal], source: str) -> Optional[HaraData]:
        """
        Create HaraData object from parsed goals.
        
        Args:
            goals: List of SafetyGoal objects
            source: Source description (e.g., "Excel file", "Working memory")
            
        Returns:
            HaraData object or None if no valid goals
        """
        if not goals:
            return None
        
        # Filter out QM goals (not safety-relevant)
        safety_relevant_goals = [g for g in goals if g.is_safety_relevant()]
        
        if not safety_relevant_goals:
            return None
        
        return HaraData(
            system=self.item_name,
            goals=safety_relevant_goals,
            source=source
        )
    
    def _normalize_asil(self, asil_text: str) -> str:
        """
        Normalize ASIL text to standard format.
        
        Args:
            asil_text: Raw ASIL text
            
        Returns:
            Normalized ASIL ('A', 'B', 'C', 'D', or 'QM')
        """
        if not asil_text:
            return 'QM'
        
        asil_upper = str(asil_text).strip().upper()
        
        # Extract ASIL level
        for level in ['D', 'C', 'B', 'A']:
            if level in asil_upper:
                return level
        
        # Check for QM
        if 'QM' in asil_upper or 'NONE' in asil_upper:
            return 'QM'
        
        return 'QM'
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        text = str(text).strip()
        
        # Remove multiple spaces
        text = ' '.join(text.split())
        
        # Remove None/null values
        if text.lower() in ['none', 'null', 'n/a', 'na']:
            return ""
        
        return text
    
    def _generate_goal_id(self, index: int) -> str:
        """
        Generate safety goal ID.
        
        Args:
            index: Goal index (1-based)
            
        Returns:
            Goal ID in format SG-XXX
        """
        return f"SG-{index:03d}"


class ParserError(Exception):
    """Exception raised for parser errors"""
    pass