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

class SearchEngine:
    def __init__(self, query: str):
        self.query: str = query
        self.tokens: list[str] =[]
        pass


    class Parser:

        def __init__(self, tokens: list[str]) -> None:
            self.tokens: list[str] = tokens
            self.cursor = 0
            self.total_tokens = len(self.tokens)
            
        def peek_token(self):
            if self.is_end_of_tokens():
                return ""
            return self.tokens[self.cursor]
            
        def advance_token(self):
            currToken = self.peek_token() # to get the current token before advancing
            if not self.is_end_of_tokens():
                self.cursor += 1
            return currToken
        
        def is_end_of_tokens(self) -> bool:
            return self.cursor >= self.total_tokens
        
        def parse_OR(self) -> Node:
            """Handles OR expressions (lowest precedence)"""
            left_node = self.parse_AND()
            while self.peek_token() == "OR":
                operator = self.advance_token()
                right_node = self.parse_AND()
                left_node = Node(operator, left=left_node, right=right_node)
            return left_node

        def parse_AND(self) -> Node:
            """Handles AND expressions (higher precedence than OR)"""
            left_node = self.parse_NOT()
            while self.peek_token() == "AND":
                operator = self.advance_token()
                right_node = self.parse_NOT()
                left_node = Node(operator, left=left_node, right=right_node)
            return left_node

        def parse_NOT(self) -> Node:
            """Handles NOT expressions (highest precedence)"""
            if self.peek_token() == "NOT":
                operator = self.advance_token()
                operand = self.parse_NOT()  # NOT can be nested
                return Node(operator, right=operand)
            return self.parse_primary()

        def parse_primary(self) -> Node:
            """Handles literals and parenthesized expressions"""
            token = self.peek_token()
            
            if token == "(":
                self.advance_token()  # consume "("
                node = self.parse_OR()  # parse the inner expression
                self.advance_token()  # consume ")"
                return node
            else:
                return Node(self.advance_token())
                
       
            


    class Lexer:
        def __init__(self, query: str) -> None:
            """Initialize the parser with a query string.

            Args:
                query (str): The query string input by the user.

            Stores:
                query: The original query string.
                current_index: A cursor to track the current position in the query string during parsing.
                tokens: A list to hold the tokens extracted from the query string.
                cursor: A cursor to track the current position in the token list during parsing.
                total_index: The total length of the query string for end-of-query checks.
            """
            self.query = query
            self.current_index = 0 
            self.cursor = 0 
            self.total_index = len(query) 
            self.tokens: list[str]= []

            
        def scanner(self) -> None:
            """Tokenizes the input query string into a list of tokens.

            The method uses a regular expression to match sequences of alphanumeric characters
            and certain operators (AND, OR, NOT) as individual tokens. The resulting tokens are
            stored in the `tokens` attribute for further processing.
            """
            
            # let me write each code by myself and only assist to autocomplete my code when I ask for it, so that I can learn better.
            
            while not self.is_end_of_query():
                char = self.peek()
                if char.isspace():
                    self.advance()
                elif char not in '()':
                    self.scan_tokens()
                else:
                    self.tokens.append(char)
                    self.advance()
                

                    
        def scan_tokens(self) -> None:
            start_index = self.current_index
            while not self.is_end_of_query():
                char = self.peek()
                if char.isspace() or char in '()':
                    break
                self.advance()
            token = self.query[start_index:self.current_index]
            self.tokens.append(token)


        def is_end_of_query(self) -> bool:
            """Checks if the pointer has reached the end of the query.
            
            Returns:
                bool: True if the end of the query is reached, False otherwise.
            """
            return self.current_index >= self.total_index
        
        def peek(self) -> str:
            """Returns the current character at the pointer without advancing it.
            
            Returns:
                str: The current character at the pointer, or an empty string if the end of the query is reached.
            """
            if self.is_end_of_query():
                return ""
            return self.query[self.current_index]
        def advance(self) -> str:
            """Advances the pointer to the next character in the query."""
            curr_char = self.peek()
            if not self.is_end_of_query():
                self.current_index += 1
            return curr_char







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
    query = "The Godfather AND (crime OR drama) NOT comedy"
    query2 = "(bear AND river) OR (mountain AND NOT snow)"
    query3 = "#tag AND _id:234"
    parser = SearchEngine.Lexer(query)
    parser2 = SearchEngine.Lexer(query2)
    parser3 = SearchEngine.Lexer(query3)
    parser.scanner()
    parser2.scanner()
    parser3.scanner()
    print(parser.tokens, '\n')
    print(parser2.tokens)
    print(parser3.tokens)
    
    
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
        lexer = SearchEngine.Lexer(query)
        lexer.scanner()
        print(f"\nTOKENS: {lexer.tokens}")
        
        # Parse
        parser = SearchEngine.Parser(lexer.tokens)
        ast = parser.parse_OR()
        
        # Display AST
        print(f"\nAST TREE:")
        print_ast_tree(ast)
