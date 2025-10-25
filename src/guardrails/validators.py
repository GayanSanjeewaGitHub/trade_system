"""
Guardrails and validation layer for input safety.
"""

import re
from typing import Dict, Any
from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class GuardrailValidator:
    """Validation and safety checks for user inputs."""
    
    def __init__(self):
        self.restricted_patterns = self._compile_restricted_patterns()
        self.profanity_list = self._load_profanity_list()
    
    def _compile_restricted_patterns(self) -> list:
        """Compile regex patterns for restricted content."""
        patterns = []
        
        # Add patterns for restricted topics
        for topic in settings.restricted_topics:
            # Case-insensitive pattern
            patterns.append(re.compile(rf'\b{re.escape(topic)}\b', re.IGNORECASE))
        
        # Add patterns for malicious content
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS attempts
            r'javascript:',  # JavaScript injection
            r'on\w+\s*=',  # Event handlers
            r'eval\s*\(',  # Eval attempts
            r'exec\s*\(',  # Exec attempts
        ]
        
        patterns.extend([re.compile(p, re.IGNORECASE) for p in malicious_patterns])
        
        return patterns
    
    def _load_profanity_list(self) -> set:
        """Load profanity word list."""
        # Basic profanity list - extend as needed
        return {
            "badword1", "badword2", "offensive1", "offensive2"
            # Add more as needed
        }
    
    async def validate_input(self, text: str) -> Dict[str, Any]:
        """
        Validate user input for safety and compliance.
        
        Args:
            text: User input text
            
        Returns:
            Dict with validation result
        """
        try:
            # Check length
            if len(text) > settings.max_message_length:
                return {
                    "valid": False,
                    "reason": f"Message too long. Maximum {settings.max_message_length} characters allowed."
                }
            
            if not text.strip():
                return {
                    "valid": False,
                    "reason": "Message cannot be empty."
                }
            
            # Check for restricted topics
            for pattern in self.restricted_patterns:
                if pattern.search(text):
                    logger.warning("Restricted content detected", pattern=pattern.pattern)
                    return {
                        "valid": False,
                        "reason": "Your message contains restricted content. Please rephrase."
                    }
            
            # Check for profanity
            profanity_score = self._check_profanity(text)
            if profanity_score > settings.profanity_threshold:
                logger.warning("Profanity detected", score=profanity_score)
                return {
                    "valid": False,
                    "reason": "Please keep the conversation professional."
                }
            
            # Check for injection attempts
            if self._check_injection_attempts(text):
                logger.warning("Injection attempt detected", text=text[:100])
                return {
                    "valid": False,
                    "reason": "Invalid input detected."
                }
            
            return {
                "valid": True,
                "reason": None
            }
            
        except Exception as e:
            logger.error("Validation error", error=str(e))
            return {
                "valid": False,
                "reason": "Validation error occurred."
            }
    
    def _check_profanity(self, text: str) -> float:
        """
        Check text for profanity.
        
        Returns:
            Profanity score between 0 and 1
        """
        words = text.lower().split()
        profane_count = sum(1 for word in words if word in self.profanity_list)
        
        if len(words) == 0:
            return 0.0
        
        return profane_count / len(words)
    
    def _check_injection_attempts(self, text: str) -> bool:
        """Check for code injection attempts."""
        # Look for common injection patterns
        injection_indicators = [
            'union select',
            'drop table',
            'insert into',
            'delete from',
            '--',
            '/*',
            '*/',
            'xp_cmdshell',
            'exec(',
            'execute(',
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in injection_indicators)
    
    async def validate_trade_parameters(
        self,
        symbol: str,
        quantity: int,
        amount: float
    ) -> Dict[str, Any]:
        """
        Validate trading parameters.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            amount: Total trade amount
            
        Returns:
            Validation result
        """
        try:
            # Validate symbol format
            if not re.match(r'^[A-Z]{1,5}$', symbol.upper()):
                return {
                    "valid": False,
                    "reason": "Invalid stock symbol format."
                }
            
            # Validate quantity
            if quantity <= 0:
                return {
                    "valid": False,
                    "reason": "Quantity must be positive."
                }
            
            # Validate trade amount limits
            if amount > settings.max_trade_amount:
                return {
                    "valid": False,
                    "reason": f"Trade amount exceeds maximum allowed: ${settings.max_trade_amount:,.2f}"
                }
            
            if amount < settings.min_trade_amount:
                return {
                    "valid": False,
                    "reason": f"Trade amount below minimum: ${settings.min_trade_amount:,.2f}"
                }
            
            return {
                "valid": True,
                "reason": None
            }
            
        except Exception as e:
            logger.error("Trade validation error", error=str(e))
            return {
                "valid": False,
                "reason": "Validation error occurred."
            }
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input by removing potentially harmful content.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text