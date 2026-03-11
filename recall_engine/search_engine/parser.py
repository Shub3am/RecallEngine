from recall_engine.search_engine.utils import Node



class Parser:
    def parse(self, tokens: list[str]) -> Node:
        self._tokens = tokens
        self._cursor = 0
        self._total_tokens = len(self._tokens)
        ast = self._parse_or()
        return ast
    
    def _peek_token(self):
        if self._is_end_of_tokens():
            return ""
        return self._tokens[self._cursor]
        
    def _advance_token(self):
        currToken = self._peek_token()  # get current token before advancing
        if not self._is_end_of_tokens():
            self._cursor += 1
        return currToken
    
    def _is_end_of_tokens(self) -> bool:
        return self._cursor >= self._total_tokens
    # Notes: NOT > AND > OR ( highest precedence to lowest precedence)        
    def _parse_or(self) -> Node:
        """Handles OR expressions (lowest precedence)"""
        left_node = self._parse_and()
        while self._peek_token() == "OR":
            operator = self._advance_token()
            right_node = self._parse_and()
            left_node = Node(operator, left=left_node, right=right_node)
        return left_node

    def _parse_and(self) -> Node:
        """Handles AND expressions (higher precedence than OR)"""
        left_node = self._parse_not()
        while self._peek_token() == "AND":
            operator = self._advance_token()
            right_node = self._parse_not()
            left_node = Node(operator, left=left_node, right=right_node)
        return left_node

    def _parse_not(self) -> Node:
        """Handles NOT expressions (highest precedence)"""
        if self._peek_token() == "NOT":
            operator = self._advance_token()
            operand = self._parse_not()  # NOT can be nested
            return Node(operator, right=operand)
        return self._parse_primary()

    def _parse_primary(self) -> Node:
        """Handles literals and parenthesized expressions"""
        token = self._peek_token()
        
        if token == "(":
            self._advance_token()  # consume "("
            node = self._parse_or()  # parse the inner expression
            self._advance_token()  # consume ")"
            return node
        else:
            return Node(self._advance_token())




# ==================== AST VISUALIZATION FUNCTIONS ====================

def print_ast_tree(node: Node, prefix: str = "", is_last: bool = True) -> None:
    """
    Prints the AST tree in a visual tree format.
    
    Args:
        node: The root node of the AST
        prefix: Prefix for spacing (used internally for recursion)
        is_last: Whether this is the last child (used internally for recursion)
    """
    if node.value is None:
        return
    
    # Print current node
    connector = "└── " if is_last else "├── "
    node_label = f"[{node.nodeType}] {node.value}"
    print(prefix + connector + node_label)
    
    # Calculate prefix for children
    extension = "    " if is_last else "│   "
    new_prefix = prefix + extension
    
    # Print left child
    if node.left is not None:
        print_ast_tree(node.left, new_prefix, node.right is None)
    
    # Print right child
    if node.right is not None:
        print_ast_tree(node.right, new_prefix, True)


def print_ast_inline(node: Node) -> str:
    """
    Prints the AST in a compact inline format.
    
    Args:
        node: The root node of the AST
        
    Returns:
        String representation of the AST
    """
    if node is None:
        return ""
    
    if node.left is None and node.right is None:
        # Leaf node (LITERAL)
        return node.value
    
    left_str = print_ast_inline(node.left) if node.left else ""
    right_str = print_ast_inline(node.right) if node.right else ""
    
    if node.value == "NOT":
        # Unary operator
        return f"NOT({right_str})"
    else:
        # Binary operators (AND, OR)
        return f"({left_str} {node.value} {right_str})"


def get_ast_depth(node: Node) -> int:
    """
    Returns the depth (height) of the AST tree.
    
    Args:
        node: The root node of the AST
        
    Returns:
        The depth of the tree
    """
    if node is None:
        return 0
    
    left_depth = get_ast_depth(node.left)
    right_depth = get_ast_depth(node.right)
    
    return 1 + max(left_depth, right_depth)



# For Testing Only
if __name__ == "__main__":    
    test_queries = [
       "The Godfather AND (crime OR drama) NOT comedy",
       "(bear AND river) OR (mountain AND NOT snow)",
       "#tag AND _id:234",
       "apple OR banana",
       "NOT word",
    ]
    for query in test_queries:
        print("\n" + "="*70)
        print(f"QUERY: {query}")
        print("="*70)
        
        # Tokenize
        from recall_engine.search_engine import lexer
        tokens = lexer.Lexer(query).tokens
        
        print(f"\nTOKENS: {tokens}")
        
        # Parse
        ast = Parser().parse(tokens)

        # # Display AST
        print(f"\nAST TREE:")
        print_ast_tree(ast)
