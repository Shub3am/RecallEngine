            
from typing import Optional


class Node:
    def __init__(self, 
                    value: str, 
                    left: Optional['Node'] = None, 
                    right: Optional['Node'] = None) -> None:
        self.nodeType = "OPERATOR" if value in ["AND", "OR", "NOT"] else "LITERAL"
        self.value = value
        self.left = left
        self.right = right