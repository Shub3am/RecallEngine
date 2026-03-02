"""Unit tests for keyword_search_cli module."""
import pytest
from unittest.mock import patch, mock_open

from recall_engine.cli.keyword_search_cli import (
    tokens_stemmer,
    clean_punctuation,
    remove_stop_words,
    standardize_texts,
    match_keyword
)

# To Run tests individually:
# example: poetry run pytest tests/test_keyword_search_cli.py::TestTokensStemmer::test_basic_stemming 

class TestTokensStemmer:
    """Test the tokens_stemmer function."""
    # poetry run pytest tests/test_keyword_search_cli.py::TestTokensStemmer::test_basic_stemming -v -s
    def test_basic_stemming(self):
        """Test basic word stemming."""
        tokens = ["running", "runs", "runner"]
        result = tokens_stemmer(tokens)
        # All should stem to 'run'
        assert "run" in result
        assert "runner" in result
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestTokensStemmer::test_empty_list -v -s
    def test_empty_list(self):
        """Test with empty token list."""
        result = tokens_stemmer([])
        assert result == []
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestTokensStemmer::test_already_stemmed -v -s
    def test_already_stemmed(self):
        """Test words that are already in root form."""
        tokens = ["cat", "dog", "run"]
        result = tokens_stemmer(tokens)
        assert len(result) == 3
        assert all(token in result for token in ["cat", "dog", "run"])
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestTokensStemmer::test_duplicate_stems -v -s
    def test_duplicate_stems(self):
        """Test that duplicate stems are removed."""
        tokens = ["running", "runner", "runs", "run"]
        result = tokens_stemmer(tokens)
        assert len(result) == 2
        assert "run" in result
        assert "runner" in result
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestTokensStemmer::test_mixed_case -v -s
    def test_mixed_case(self):
        """Test that case is normalized during stemming."""
        tokens = ["Running", "RUNS", "runner"]
        result = tokens_stemmer(tokens)
        assert len(result) == 2
        assert "run" in result
        assert "runner" in result


class TestCleanPunctuation:
    """Test the clean_punctuation function."""
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestCleanPunctuation::test_remove_basic_punctuation -v -s
    def test_remove_basic_punctuation(self):
        """Test removal of common punctuation marks."""
        text = "Hello, world! How are you?"
        result = clean_punctuation(text)
        assert result == "Hello world How are you"
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestCleanPunctuation::test_no_punctuation -v -s
    def test_no_punctuation(self):
        """Test text without punctuation."""
        text = "Hello world"
        result = clean_punctuation(text)
        assert result == "Hello world"
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestCleanPunctuation::test_only_punctuation -v -s
    def test_only_punctuation(self):
        """Test string with only punctuation."""
        text = "!@#$%^&*()"
        result = clean_punctuation(text)
        assert result == ""
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestCleanPunctuation::test_mixed_punctuation -v -s
    def test_mixed_punctuation(self):
        """Test various punctuation marks."""
        text = "It's a test: brackets [here], quotes \"there\", and-dashes."
        result = clean_punctuation(text)
        assert "'" not in result
        assert '"' not in result
        assert '[' not in result
        assert '-' not in result
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestCleanPunctuation::test_empty_string -v -s
    def test_empty_string(self):
        """Test with empty string."""
        result = clean_punctuation("")
        assert result == ""


class TestRemoveStopWords:
    """Test the remove_stop_words function."""
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestRemoveStopWords::test_basic_stop_word_removal -v -s
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_basic_stop_word_removal(self, mock_get_stop_words):
        """Test removal of common stop words."""
        mock_get_stop_words.return_value = ["the", "is", "a", "and"]
        tokens = ["the", "cat", "is", "on", "a", "mat"]
        result = remove_stop_words(tokens)
        assert "the" not in result
        assert "is" not in result
        assert "a" not in result
        assert "cat" in result
        assert "mat" in result
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestRemoveStopWords::test_no_stop_words -v -s
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_no_stop_words(self, mock_get_stop_words):
        """Test with no stop words in input."""
        mock_get_stop_words.return_value = ["the", "is", "a"]
        tokens = ["cat", "dog", "mouse"]
        result = remove_stop_words(tokens)
        assert len(result) == 3
        assert result == tokens
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestRemoveStopWords::test_all_stop_words -v -s
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_all_stop_words(self, mock_get_stop_words):
        """Test when all tokens are stop words."""
        mock_get_stop_words.return_value = ["the", "is", "a", "on"]
        tokens = ["the", "is", "a", "on"]
        result = remove_stop_words(tokens)
        assert len(result) == 0
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestRemoveStopWords::test_empty_token_list -v -s
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_empty_token_list(self, mock_get_stop_words):
        """Test with empty token list."""
        mock_get_stop_words.return_value = ["the", "is"]
        result = remove_stop_words([])
        assert result == []


class TestStandardizeTexts:
    """Test the standardize_texts function."""
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestStandardizeTexts::test_full_normalization_pipeline -v -s
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_full_normalization_pipeline(self, mock_get_stop_words):
        """Test complete text normalization."""
        mock_get_stop_words.return_value = ["the", "is", "a"]
        text = "The Running Dogs!"
        result = standardize_texts(text)
        # Should be lowercase, punctuation removed, stop words removed, and stemmed
        assert isinstance(result, list)
        assert len(result) > 0
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestStandardizeTexts::test_empty_string -v -s
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_empty_string(self, mock_get_stop_words):
        """Test with empty string."""
        mock_get_stop_words.return_value = ["the"]
        result = standardize_texts("")
        assert isinstance(result, list)
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestStandardizeTexts::test_complex_sentence -v -s
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_complex_sentence(self, mock_get_stop_words):
        """Test with a complex sentence."""
        mock_get_stop_words.return_value = ["the", "is", "a", "in"]
        text = "The movie is playing in the theater!"
        result = standardize_texts(text)
        # Should process multiple words
        assert isinstance(result, list)
        # Stop words should be removed
        assert "the" not in [token.lower() for token in result]


class TestMatchKeyword:
    """Test the match_keyword function."""
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestMatchKeyword::test_exact_match -v -s
    def test_exact_match(self):
        """Test exact keyword match."""
        assert match_keyword("cat", "cat") == True
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestMatchKeyword::test_substring_match -v -s
    def test_substring_match(self):
        """Test substring match."""
        assert match_keyword("cat", "category") == True
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestMatchKeyword::test_no_match -v -s
    def test_no_match(self):
        """Test when keyword is not found."""
        assert match_keyword("dog", "cat") == False
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestMatchKeyword::test_case_insensitive_match -v -s
    def test_case_insensitive_match(self):
        """Test case-insensitive matching."""
        assert match_keyword("CAT", "cat") == True
        assert match_keyword("cat", "CAT") == True
        assert match_keyword("CaT", "cAt") == True
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestMatchKeyword::test_empty_strings -v -s
    def test_empty_strings(self):
        """Test with empty strings."""
        assert match_keyword("", "test") == True  # Empty string is substring of any string
        assert match_keyword("test", "") == False
    
    # poetry run pytest tests/test_keyword_search_cli.py::TestMatchKeyword::test_special_characters -v -s
    def test_special_characters(self):
        """Test with special characters."""
        assert match_keyword("test!", "this is a test!") == True
        assert match_keyword("test", "test!") == True
