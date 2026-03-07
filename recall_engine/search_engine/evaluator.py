from recall_engine.search_engine.parser import Node
class Evaluator:
    def __init__(self, index: dict[str, list[str] ]) -> None:
        self.index = index

    def evaluate(self, ast: Node) -> set[str]:
        """Evaluate a parsed query AST against the index and return matching document IDs.
        
        Args:
            ast: The root node of the parsed query AST to evaluate.
        Returns:
            A set of document IDs matching the query.
        """
        if ast.nodeType == "LITERAL":
            return self._eval_literal(ast.value)
        elif ast.nodeType == "OPERATOR":
            left_result: set[str] = self.evaluate(ast.left) if ast.left else set()
            right_result: set[str] = self.evaluate(ast.right) if ast.right else set()
            return self._eval_operator(ast.value, left_result, right_result)
        else:
            raise ValueError(f"Unknown node type: {ast.nodeType}")
    
    def _eval_operator(self, operator: str, left_result: set[str], right_result: set[str]) -> set[str]:
        """Evaluate a logical operator (AND, OR, NOT) on two sets of document IDs.
        
        Args:
            operator: The logical operator to apply ("AND", "OR", "NOT").
            left_result: The set of document IDs from the left operand.
            right_result: The set of document IDs from the right operand.
        
        Returns:
            A set of document IDs resulting from applying the operator to the operands.
        """
        if operator == "AND":
            return left_result.intersection(right_result)
        elif operator == "OR":
            return left_result.union(right_result)
        elif operator == "NOT":
            return left_result.difference(right_result)
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    def _eval_literal(self, literal: str) -> set[str]:
        """Evaluate a literal token by retrieving the set of document IDs containing it.
        
        Args:
            literal: The literal token to evaluate.
        
        Returns:
            A set of document IDs that contain the literal token.
        """
        return set(self.index.get(literal, []))