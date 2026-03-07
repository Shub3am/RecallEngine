
class Parser:
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

# For Testing Only
if __name__ == "__main__":
    query = "The Godfather AND (crime OR drama) NOT comedy"
    query2 = "(bear AND river) OR (mountain AND NOT snow)"
    query3 = "#tag AND _id:234"
    parser = Parser(query)
    parser2 = Parser(query2)
    parser3 = Parser(query3)
    parser.scanner()
    parser2.scanner()
    parser3.scanner()
    print(parser.tokens, '\n')
    print(parser2.tokens)
    print(parser3.tokens)