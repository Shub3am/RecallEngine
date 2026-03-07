             
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
        self._current_index = 0 # Pointer to track current position in the query string
        self._total_index = len(query) 
        self.tokens: list[str]= self.scanner()

    def scanner(self) -> list[str]:
        """Tokenizes the input query string into a list of tokens.

        The method uses a regular expression to match sequences of alphanumeric characters
        and certain operators (AND, OR, NOT) as individual tokens. The resulting tokens are
        stored in the `tokens` attribute for further processing.
        """
        
        # let me write each code by myself and only assist to autocomplete my code when I ask for it, so that I can learn better.
        tokens: list[str] = []
        while not self._is_end_of_query():
            char = self._peek()
            if char.isspace():
                self._advance()
            elif char not in '()':
                tokens.append(self._scan_tokens())
            else:
                tokens.append(char)
                self._advance()
        return tokens
                
    def _scan_tokens(self) -> str:
        start_index = self._current_index
        while not self._is_end_of_query():
            char = self._peek()
            if char.isspace() or char in '()':
                break
            self._advance()
        token = self.query[start_index:self._current_index]
        return token


    def _is_end_of_query(self) -> bool:
        """Checks if the pointer has reached the end of the query.
        
        Returns:
            bool: True if the end of the query is reached, False otherwise.
        """
        return self._current_index >= self._total_index
    
    def _peek(self) -> str:
        """Returns the current character at the pointer without advancing it.
        
        Returns:
            str: The current character at the pointer, or an empty string if the end of the query is reached.
        """
        if self._is_end_of_query():
            return ""
        return self.query[self._current_index]
    def _advance(self) -> str:
        """Advances the pointer to the next character in the query."""
        curr_char = self._peek()
        if not self._is_end_of_query():
            self._current_index += 1
        return curr_char



if __name__ == "__main__":
    test_queries = [
       "The Godfather AND (crime OR drama) NOT comedy",
       "(bear AND river) OR (mountain AND NOT snow)",
       "#tag AND _id:234",
       "apple OR banana",
       "NOT word",
    ]
    for query in test_queries:
        lexer = Lexer(query)
        lexer.scanner()
        print(f"Query: {query}")
        print(f"Tokens: {lexer.tokens}")
        print("-" * 40)