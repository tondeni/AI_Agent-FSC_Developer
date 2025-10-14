"""
Text Utilities for FSC Developer Plugin
Provides string manipulation and formatting functions
"""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text (replace multiple spaces/newlines with single space).
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace characters with single space
    normalized = re.sub(r'\s+', ' ', text)
    
    # Trim leading and trailing whitespace
    return normalized.strip()


def clean_text(text: str) -> str:
    """
    Clean text by removing special characters while preserving readability.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove control characters but keep basic punctuation
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    cleaned = normalize_whitespace(cleaned)
    
    return cleaned


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length, adding suffix if truncated.
    
    Args:
        text: Input text
        max_length: Maximum length (default: 100)
        suffix: Suffix to add if truncated (default: "...")
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rstrip() + suffix


def extract_id_from_text(text: str, prefix: str = "") -> Optional[str]:
    """
    Extract an ID from text (e.g., "SG-01" from "Safety Goal SG-01: ...").
    
    Args:
        text: Input text
        prefix: Expected ID prefix (e.g., "SG", "FSR")
        
    Returns:
        Extracted ID or None
    """
    if not text:
        return None
    
    # Pattern: prefix-digits or prefix digits
    if prefix:
        pattern = rf'{prefix}[-_\s]*(\d+)'
    else:
        # Generic pattern for IDs
        pattern = r'([A-Z]+[-_]?\d+)'
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(0).upper().replace(' ', '-')
    
    return None


def generate_id(prefix: str, number: int, digits: int = 2) -> str:
    """
    Generate a standardized ID with prefix and zero-padded number.
    
    Args:
        prefix: ID prefix (e.g., "SG", "FSR")
        number: Sequence number
        digits: Number of digits for padding (default: 2)
        
    Returns:
        Generated ID (e.g., "SG-01")
    """
    return f"{prefix}-{str(number).zfill(digits)}"


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    # Split on period, exclamation, or question mark followed by space and capital letter
    # or end of string
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$', text)
    
    # Clean and filter empty sentences
    return [s.strip() for s in sentences if s.strip()]


def extract_bullet_points(text: str) -> List[str]:
    """
    Extract bullet points from text.
    
    Args:
        text: Input text with bullet points
        
    Returns:
        List of bullet point contents
    """
    if not text:
        return []
    
    # Split by newlines
    lines = text.split('\n')
    
    bullet_points = []
    bullet_patterns = [r'^\s*[-•*]\s+', r'^\s*\d+\.\s+', r'^\s*[a-z]\)\s+']
    
    for line in lines:
        # Check if line starts with bullet marker
        for pattern in bullet_patterns:
            if re.match(pattern, line):
                # Remove bullet marker
                content = re.sub(pattern, '', line).strip()
                if content:
                    bullet_points.append(content)
                break
    
    return bullet_points


def format_as_bullet_list(items: List[str], bullet_char: str = "•") -> str:
    """
    Format a list of items as a bullet list.
    
    Args:
        items: List of items
        bullet_char: Bullet character to use (default: "•")
        
    Returns:
        Formatted bullet list string
    """
    if not items:
        return ""
    
    return "\n".join([f"{bullet_char} {item}" for item in items])


def format_as_numbered_list(items: List[str]) -> str:
    """
    Format a list of items as a numbered list.
    
    Args:
        items: List of items
        
    Returns:
        Formatted numbered list string
    """
    if not items:
        return ""
    
    return "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])


def wrap_text(text: str, width: int = 80, indent: str = "") -> str:
    """
    Wrap text to specified width with optional indentation.
    
    Args:
        text: Input text
        width: Line width (default: 80)
        indent: String to use for indentation (default: "")
        
    Returns:
        Wrapped text
    """
    if not text:
        return ""
    
    words = text.split()
    lines = []
    current_line = indent
    
    for word in words:
        # Check if adding word would exceed width
        if len(current_line) + len(word) + 1 <= width:
            if current_line == indent:
                current_line += word
            else:
                current_line += " " + word
        else:
            # Start new line
            if current_line.strip():
                lines.append(current_line)
            current_line = indent + word
    
    # Add last line
    if current_line.strip():
        lines.append(current_line)
    
    return "\n".join(lines)


def capitalize_first(text: str) -> str:
    """
    Capitalize the first letter of text.
    
    Args:
        text: Input text
        
    Returns:
        Text with first letter capitalized
    """
    if not text:
        return ""
    
    return text[0].upper() + text[1:] if len(text) > 1 else text.upper()


def to_title_case(text: str, preserve_acronyms: bool = True) -> str:
    """
    Convert text to title case.
    
    Args:
        text: Input text
        preserve_acronyms: Whether to preserve all-caps acronyms (default: True)
        
    Returns:
        Title-cased text
    """
    if not text:
        return ""
    
    # Words that should remain lowercase in titles
    lowercase_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 
                      'of', 'on', 'or', 'the', 'to', 'up', 'via'}
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Check if it's an acronym (all uppercase)
        if preserve_acronyms and word.isupper() and len(word) > 1:
            result.append(word)
        # First and last words should always be capitalized
        elif i == 0 or i == len(words) - 1:
            result.append(word.capitalize())
        # Small words should be lowercase (unless first/last)
        elif word.lower() in lowercase_words:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract potential keywords from text (simple extraction).
    
    Args:
        text: Input text
        min_length: Minimum word length to consider (default: 3)
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Remove punctuation and split
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Common stop words to exclude
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that',
                  'these', 'those', 'it', 'its'}
    
    # Filter and deduplicate
    keywords = []
    seen = set()
    
    for word in words:
        if len(word) >= min_length and word not in stop_words and word not in seen:
            keywords.append(word)
            seen.add(word)
    
    return keywords


def highlight_text(text: str, keywords: List[str], marker: str = "**") -> str:
    """
    Highlight keywords in text with specified marker.
    
    Args:
        text: Input text
        keywords: List of keywords to highlight
        marker: Marker to use (default: "**" for markdown bold)
        
    Returns:
        Text with highlighted keywords
    """
    if not text or not keywords:
        return text
    
    result = text
    
    for keyword in keywords:
        # Case-insensitive replace while preserving original case
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        result = pattern.sub(f"{marker}\\g<0>{marker}", result)
    
    return result


def create_table_row(columns: List[str], widths: Optional[List[int]] = None, 
                     separator: str = " | ") -> str:
    """
    Create a formatted table row.
    
    Args:
        columns: List of column values
        widths: Optional list of column widths (default: auto)
        separator: Column separator (default: " | ")
        
    Returns:
        Formatted table row string
    """
    if not columns:
        return ""
    
    if widths and len(widths) == len(columns):
        # Pad columns to specified widths
        padded = [str(col).ljust(width) for col, width in zip(columns, widths)]
    else:
        # No padding
        padded = [str(col) for col in columns]
    
    return separator.join(padded)


def create_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    Create a markdown-formatted table.
    
    Args:
        headers: List of header strings
        rows: List of row data (each row is a list of strings)
        
    Returns:
        Markdown table string
    """
    if not headers:
        return ""
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Create table
    lines = []
    
    # Header row
    lines.append(create_table_row(headers, widths, " | "))
    
    # Separator row
    separator = ["-" * width for width in widths]
    lines.append(create_table_row(separator, widths, " | "))
    
    # Data rows
    for row in rows:
        # Ensure row has same number of columns as headers
        padded_row = row + [""] * (len(headers) - len(row))
        lines.append(create_table_row(padded_row[:len(headers)], widths, " | "))
    
    return "\n".join(lines)


def slugify(text: str, separator: str = "-") -> str:
    """
    Convert text to a URL-friendly slug.
    
    Args:
        text: Input text
        separator: Separator character (default: "-")
        
    Returns:
        Slugified text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and special characters with separator
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', separator, slug)
    
    # Remove leading/trailing separators
    slug = slug.strip(separator)
    
    return slug


def similarity_ratio(text1: str, text2: str) -> float:
    """
    Calculate simple similarity ratio between two texts (0.0 to 1.0).
    Uses Jaccard similarity on words.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity ratio (0.0 = no similarity, 1.0 = identical)
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to sets of words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def format_timestamp(dt: Optional[datetime] = None, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object as a string.
    
    Args:
        dt: Datetime object (default: now)
        format: Format string (default: ISO-like format)
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    
    return dt.strftime(format)


def parse_key_value_pairs(text: str, delimiter: str = ":") -> Dict[str, str]:
    """
    Parse key-value pairs from text.
    
    Args:
        text: Input text with key-value pairs
        delimiter: Delimiter between key and value (default: ":")
        
    Returns:
        Dictionary of key-value pairs
    """
    if not text:
        return {}
    
    pairs = {}
    lines = text.split('\n')
    
    for line in lines:
        if delimiter in line:
            parts = line.split(delimiter, 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key:
                    pairs[key] = value
    
    return pairs


def indent_text(text: str, spaces: int = 4) -> str:
    """
    Indent all lines of text by specified number of spaces.
    
    Args:
        text: Input text
        spaces: Number of spaces for indentation (default: 4)
        
    Returns:
        Indented text
    """
    if not text:
        return ""
    
    indent = " " * spaces
    lines = text.split('\n')
    
    return '\n'.join([indent + line for line in lines])


def remove_markdown(text: str) -> str:
    """
    Remove markdown formatting from text.
    
    Args:
        text: Input text with markdown
        
    Returns:
        Plain text without markdown
    """
    if not text:
        return ""
    
    # Remove headers
    result = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold and italic
    result = re.sub(r'\*\*(.+?)\*\*', r'\1', result)
    result = re.sub(r'\*(.+?)\*', r'\1', result)
    result = re.sub(r'__(.+?)__', r'\1', result)
    result = re.sub(r'_(.+?)_', r'\1', result)
    
    # Remove links [text](url)
    result = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', result)
    
    # Remove inline code
    result = re.sub(r'`(.+?)`', r'\1', result)
    
    return result


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    if not text:
        return 0
    
    # Remove extra whitespace and split
    words = text.split()
    
    return len(words)


def abbreviate(text: str, keep_uppercase: bool = True) -> str:
    """
    Create an abbreviation from text (first letter of each word).
    
    Args:
        text: Input text
        keep_uppercase: Whether to keep uppercase letters from original (default: True)
        
    Returns:
        Abbreviation
    """
    if not text:
        return ""
    
    words = text.split()
    
    if keep_uppercase:
        # Take first letter of each word, preserve case
        abbr = ''.join([word[0] for word in words if word])
    else:
        # Take first letter and convert to uppercase
        abbr = ''.join([word[0].upper() for word in words if word])
    
    return abbr