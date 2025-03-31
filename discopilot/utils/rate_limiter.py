import time
from collections import deque

class RateLimiter:
    """
    A utility class to handle rate limiting for API calls
    """
    
    def __init__(self, max_calls, period):
        """
        Initialize the rate limiter
        
        Args:
            max_calls (int): Maximum number of calls allowed in the period
            period (int): Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.cooldown_until = 0
    
    def add_call(self):
        """Record an API call"""
        now = time.time()
        self.calls.append(now)
        
        # Remove calls older than the period
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
    
    def is_limited(self):
        """Check if rate limited"""
        now = time.time()
        
        # Check if we're in a cooldown period
        if now < self.cooldown_until:
            return True
        
        # Clean up old calls
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        
        # Check if we've exceeded the maximum calls
        return len(self.calls) >= self.max_calls
    
    def set_cooldown(self, seconds):
        """Set a cooldown period"""
        self.cooldown_until = time.time() + seconds
    
    def get_remaining_calls(self):
        """Get the number of remaining calls allowed"""
        self.is_limited()  # Clean up old calls
        return max(0, self.max_calls - len(self.calls))
    
    def get_reset_time(self):
        """Get the time until rate limit resets"""
        now = time.time()
        
        if self.cooldown_until > now:
            return self.cooldown_until - now
        
        if not self.calls:
            return 0
        
        oldest_call = self.calls[0]
        return max(0, (oldest_call + self.period) - now)
