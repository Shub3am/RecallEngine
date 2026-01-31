import re 

class Parser:
    @staticmethod
    def parse_query(query):
        # This is a very basic parser that splits the query into words and identifies potential operations.
        # In a real implementation, this would be much more complex and would likely involve natural language processing.
        
        # For demonstration, let's assume we are looking for operations like "AND", "OR", "NOT"
        operations = re.findall(r'\b(AND|OR|NOT)\b', query, re.IGNORECASE)
        
        # Remove operations from the query to get the actual search terms
        search_terms = re.sub(r'\b(AND|OR|NOT)\b', '', query, flags=re.IGNORECASE).strip()
        
        return {
            'search_terms': search_terms,
            'operations': operations
        }