"""Unit tests for misc module."""
import pytest
from unittest.mock import patch, mock_open

from recall_engine.cli.misc import get_stop_words, dataset_loader


class TestGetStopWords:
    """Test the get_stop_words function."""
    
    def test_reads_stop_words_file(self):
        """Test that stop words are read from file correctly."""
        mock_file_content = "the\nis\na\nand\nor"
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = get_stop_words()
            assert isinstance(result, list)
            assert len(result) == 5
            assert "the" in result
            assert "is" in result
            assert "a" in result
    
    def test_empty_file(self):
        """Test with empty stop words file."""
        with patch('builtins.open', mock_open(read_data="")):
            result = get_stop_words()
            assert isinstance(result, list)
            assert len(result) <= 1  # May have empty string
    
    def test_file_not_found(self):
        """Test behavior when file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(SystemExit):
                get_stop_words()
    
    def test_permission_error(self):
        """Test behavior when file cannot be read due to permissions."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(SystemExit):
                get_stop_words()
    
    def test_strips_whitespace(self):
        """Test that whitespace is handled correctly."""
        mock_file_content = "word1\nword2\nword3\n"
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = get_stop_words()
            # splitlines should handle the newlines
            assert "word1" in result
            assert "word3" in result


class TestDatasetLoader:
    """Test the dataset_loader function."""
    
    def test_loads_file_content(self):
        """Test that file content is loaded correctly."""
        mock_content = '{"movies": [{"title": "Test Movie"}]}'
        with patch('builtins.open', mock_open(read_data=mock_content)):
            result = dataset_loader("test.json")
            assert result == mock_content
    
    def test_loads_different_file_types(self):
        """Test loading different file types."""
        test_content = "Some text content"
        with patch('builtins.open', mock_open(read_data=test_content)):
            result = dataset_loader("test.txt")
            assert result == test_content
    
    def test_file_not_found(self):
        """Test behavior when file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(SystemExit):
                dataset_loader("nonexistent.json")
    
    def test_permission_error(self):
        """Test behavior when file cannot be read."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(SystemExit):
                dataset_loader("protected.json")
    
    def test_empty_file(self):
        """Test loading empty file."""
        with patch('builtins.open', mock_open(read_data="")):
            result = dataset_loader("empty.json")
            assert result == ""
    
    def test_large_file_content(self):
        """Test loading larger file content."""
        large_content = "x" * 10000
        with patch('builtins.open', mock_open(read_data=large_content)):
            result = dataset_loader("large.txt")
            assert len(result) == 10000
