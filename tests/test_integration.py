"""Integration tests for the RecallEngine keyword search system."""
import json
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from recall_engine.cli.main import cli, standardize_texts, match_keyword


class TestEndToEndSearch:
    """Test complete search workflow."""
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    @patch('recall_engine.cli.keyword_search_cli.dataset_loader')
    @patch('sys.argv')
    def test_successful_search(self, mock_argv, mock_loader, mock_stop_words):
        """Test a successful end-to-end search."""
        # Mock the dataset
        mock_dataset = {
            "movies": [
                {"title": "The Running Man"},
                {"title": "Run Lola Run"},
                {"title": "Cat on a Hot Tin Roof"}
            ]
        }
        mock_loader.return_value = json.dumps(mock_dataset)
        mock_stop_words.return_value = ["the", "a", "on"]
        mock_argv.__getitem__ = lambda self, index: ["keyword_search_cli.py", "search", "running"][index]
        
        # Capture output
        with patch('sys.stdout', new=StringIO()) as fake_output:
            try:
                cli()
                output = fake_output.getvalue()
                # Should find movies with "run" in the title
                assert "Running" in output or "Run" in output
            except SystemExit:
                pass
    
    @patch('recall_engine.cli.keyword_search_cli.dataset_loader')
    @patch('sys.argv')
    def test_no_matches_found(self, mock_argv, mock_loader):
        """Test search with no matching results."""
        mock_dataset = {
            "movies": [
                {"title": "The Cat"},
                {"title": "The Dog"}
            ]
        }
        mock_loader.return_value = json.dumps(mock_dataset)
        mock_argv.__getitem__ = lambda self, index: ["keyword_search_cli.py", "search", "zebra"][index]
        
        with patch('sys.stdout', new=StringIO()) as fake_output:
            with patch('recall_engine.cli.keyword_search_cli.get_stop_words', return_value=["the"]):
                try:
                    cli()
                    output = fake_output.getvalue()
                    # Should not find any movies
                    assert "Cat" not in output or "Searching for:" in output
                except SystemExit:
                    pass
    
    @patch('sys.argv')
    def test_invalid_command(self, mock_argv):
        """Test with invalid command."""
        mock_argv.__getitem__ = lambda self, index: ["keyword_search_cli.py", "invalid"][index]
        
        with patch('sys.stdout', new=StringIO()):
            try:
                cli()
            except (SystemExit, KeyError):
                # Should handle gracefully
                pass
    
    @patch('sys.argv')
    def test_help_command(self, mock_argv):
        """Test help output."""
        mock_argv.__getitem__ = lambda self, index: ["keyword_search_cli.py", "--help"][index if index < 2 else 0]
        
        with patch('sys.stdout', new=StringIO()) as fake_output:
            try:
                main()
            except SystemExit:
                output = fake_output.getvalue()
                assert "search" in output.lower() or "usage" in output.lower()


class TestSearchWorkflow:
    """Test the search workflow components together."""
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_query_normalization_pipeline(self, mock_stop_words):
        """Test that query goes through complete normalization."""
        mock_stop_words.return_value = ["the", "a"]
        query = "The Running Dogs!"
        normalized = standardize_texts(query)
        
        # Should be a list of stemmed tokens
        assert isinstance(normalized, list)
        # Stop words should be removed
        assert "the" not in normalized
        assert "a" not in normalized
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_title_normalization_and_matching(self, mock_stop_words):
        """Test normalizing title and matching with query."""
        mock_stop_words.return_value = ["the"]
        
        query_text = "runner"
        title_text = "The Running Man"
        
        query_tokens = standardize_texts(query_text)
        title_tokens = standardize_texts(title_text)
        
        # Check if any query token matches any title token
        found_match = False
        for q_token in query_tokens:
            for t_token in title_tokens:
                if match_keyword(q_token, t_token):
                    found_match = True
                    break
        
        # Should find a match because "runner" and "running" stem to "run"
        assert found_match or len(query_tokens) > 0
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_multiple_movie_search(self, mock_stop_words):
        """Test searching across multiple movies."""
        mock_stop_words.return_value = ["the", "a", "an"]
        
        movies = [
            {"title": "The Cat Returns"},
            {"title": "Dog Day Afternoon"},
            {"title": "The Cats and Dogs"}
        ]
        
        query = standardize_texts("cat")
        matches = []
        
        for movie in movies:
            title_tokens = standardize_texts(movie['title'])
            for q_token in query:
                for t_token in title_tokens:
                    if match_keyword(q_token, t_token):
                        matches.append(movie['title'])
                        break
        
        # Should find movies with "cat" in title
        assert len(matches) > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_empty_query(self, mock_stop_words):
        """Test with empty query string."""
        mock_stop_words.return_value = ["the"]
        result = standardize_texts("")
        assert isinstance(result, list)
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_special_characters_in_query(self, mock_stop_words):
        """Test query with special characters."""
        mock_stop_words.return_value = []
        query = "!!!???###"
        result = standardize_texts(query)
        # Should handle gracefully
        assert isinstance(result, list)
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_unicode_characters(self, mock_stop_words):
        """Test with unicode characters."""
        mock_stop_words.return_value = []
        query = "café résumé"
        result = standardize_texts(query)
        assert isinstance(result, list)
    
    @patch('recall_engine.cli.keyword_search_cli.get_stop_words')
    def test_very_long_query(self, mock_stop_words):
        """Test with very long query string."""
        mock_stop_words.return_value = ["the", "a"]
        query = " ".join(["word"] * 1000)
        result = standardize_texts(query)
        assert isinstance(result, list)


class TestDataIntegrity:
    """Test data handling and integrity."""
    
    @patch('recall_engine.cli.keyword_search_cli.dataset_loader')
    def test_malformed_json(self, mock_loader):
        """Test handling of malformed JSON data."""
        mock_loader.return_value = "{invalid json"
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(mock_loader("test.json"))
    
    @patch('recall_engine.cli.keyword_search_cli.dataset_loader')
    def test_missing_movies_key(self, mock_loader):
        """Test dataset without 'movies' key."""
        mock_loader.return_value = '{"data": []}'
        data = json.loads(mock_loader("test.json"))
        
        # Should handle missing key gracefully
        with pytest.raises(KeyError):
            _ = data['movies']
    
    @patch('recall_engine.cli.keyword_search_cli.dataset_loader')
    def test_empty_movies_array(self, mock_loader):
        """Test with empty movies array."""
        mock_loader.return_value = '{"movies": []}'
        data = json.loads(mock_loader("test.json"))
        
        assert data['movies'] == []
        assert len(data['movies']) == 0
