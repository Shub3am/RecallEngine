from nltk.stem import PorterStemmer
import string
from pathlib import Path
from typing import cast

class Tokenizer():
    """
    A class to tokenize the documents. It can be used to tokenize the documents while building the index and also while querying the index. It can be used to remove stop words and also to perform stemming and lemmatization. It can be used to perform other preprocessing steps as well.
        """
    _PUNCT_TABLE = str.maketrans("", "", string.punctuation)

    def __init__(self, stop_words: list[str] | None = None, stop_words_path: str | None = None) -> None:
        self.stop_words = stop_words if stop_words is not None else self._load_stop_words(stop_words_path)
        self._stop_word_set = set(self.stop_words)
        self.stemmer = PorterStemmer()

    @staticmethod
    def _default_stop_words_path() -> Path:
        return Path(__file__).resolve().parent / "stop_words.txt"

    def _load_stop_words(self, stop_words_path: str | None) -> list[str]:
        path = Path(stop_words_path) if stop_words_path else self._default_stop_words_path()
        try:
            with path.open("r", encoding="utf-8") as words_file:
                return words_file.read().splitlines()
        except OSError as exc:
            raise RuntimeError(f"Unable to load stop words from '{path}': {exc}") from exc
    def tokenize(self, content: str) -> list[str]:
        """ 
        Normalize text through a multi-step pipeline for search matching.
        
        Pipeline: lowercase → remove punctuation → tokenize → remove stop words → stem
        
        Args:
            content: Raw text string to normalize
            
        Returns:
            List of normalized, stemmed tokens
        """
        
        # Sample input: "The quick brown fox jumps over the lazy dog!"
        base = content.lower()
        
        # After lowercasing: "the quick brown fox jumps over the lazy dog!"
        base = self._clean_punctuation(base)
        # After punctuation removal: "the quick brown fox jumps over the lazy dog"
        base = base.split()
        # After Splitting: ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
        base = self._remove_stop_words(base)
        # After Stop Word Removal (assuming "the", "over" are stop words): ["quick", "brown", "fox", "jumps", "lazy", "dog"]
        base = self._tokens_stemmer(base)
        # After Stemming (e.g., "jumps" → "jump"): ["quick", "brown", "fox", "jump", "lazi", "dog"]
        return base

    def tokenize_with_frequency(self, content: str) -> list[str]:
        """Normalize text while preserving repeated terms.

        Boolean matching only needs term presence, so `tokenize()` removes
        duplicates. Ranked retrieval needs real term frequency, so this method
        keeps duplicates after the same normalization steps.
        """
        normalized = content.lower()
        normalized = self._clean_punctuation(normalized)
        raw_tokens = normalized.split()
        filtered_tokens = self._remove_stop_words(raw_tokens)
        return [cast(str, self.stemmer.stem(token, to_lowercase=True)) for token in filtered_tokens]

           
    def _tokens_stemmer(self, tokens: list[str]) -> list[str]:
        """Reduce tokens to their root forms using Porter Stemming algorithm.
        
        Args:
            tokens: List of word tokens to stem
            
        Returns:
            List of unique stemmed tokens (duplicates removed via dict)
        """
        stemmed_tokens: dict[str, str] = {}
        for token in tokens:
            stemmed_word = cast(str, self.stemmer.stem(token,  to_lowercase=True))
            stemmed_tokens[stemmed_word] = ""
        return list(stemmed_tokens.keys())

    def _clean_punctuation(self, content: str) -> str:
        """Remove all punctuation characters from the given text.
        
        Args:
            content: String containing text to clean
            
       punctuation table: {'.': '', ',': '', '!': '', '?': '', ...} mapping each punctuation character to an empty string for removal
        maketrans: creates a mapping table for str.translate to replace each punctuation character with an empty string, effectively removing it from the content. The resulting string is returned without any punctuation.
        translate: method applies the translation table to the content, replacing all punctuation characters with an empty string, thus removing them from the content. The cleaned content is then returned.

    
        Returns:
            String with all punctuation removed
        """
        return content.translate(self._PUNCT_TABLE)

    def _remove_stop_words(self, content_tokens: list[str]) -> list[str]:
        """Filter out common stop words from token list.
        
        Args:
            content_tokens: List of word tokens to filter
            
        Returns:
            List of tokens with stop words removed
        """
        return [word for word in content_tokens if word not in self._stop_word_set]
            
    @staticmethod
    def match_keyword(query: str, content: str) -> bool:
        """Check if query string exists as substring in content (case-insensitive).
        
        Args:
            query: Search term to look for
            content: Text to search within
            
        Returns:
            True if query found in content, False otherwise
        """
        return query.lower() in content.lower()
            