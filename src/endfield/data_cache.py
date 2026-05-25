from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional , Dict , Any , Generic , TypeVar
from collections import defaultdict

T = TypeVar('T', bound=BaseModel)

class CacheEntry(Generic[T]):
    def __init__(self, data: T, ttl: int):
        self.data = data
        self.expire_at = datetime.now().timestamp() + ttl
        
class CacheManager(Generic[T]):
    def __init__(self):
        self.cache: Dict[str, CacheEntry[T]] = {}
    
    def set(self, key: str, data: T, ttl: int=300):
        self.cache[key] = CacheEntry(data, ttl)
    
    def get(self, key: str) -> Optional[T]:
        entry = self.cache.get(key)
        if entry and entry.expire_at > datetime.now().timestamp():
            return entry.data
        elif entry:
            del self.cache[key]  
        return None