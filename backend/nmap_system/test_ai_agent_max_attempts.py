#!/usr/bin/env python3
"""
Test AI Agent retry logic

Issue 3: Rename max_retries to max_attempts for clarity
- max_retries=2 was confusing (2 total attempts or 2 retries?)
- max_attempts=2 clearly means 2 total attempts (1 initial + 1 retry)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ai_agent import call_ollama


class TestCallOllamaMaxAttempts:
    """Test the max_attempts parameter in call_ollama function"""

    @patch('ai_agent.requests.post')
    def test_max_attempts_parameter_exists(self, mock_post):
        """
        Test that max_attempts parameter is accepted (not max_retries).
        
        This test will FAIL until we rename the parameter from max_retries to max_attempts.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'test response'}
        mock_post.return_value = mock_response

        # This should work with max_attempts parameter
        result = call_ollama("test prompt", max_attempts=2)

        assert result == 'test response'
        mock_post.assert_called_once()

    @patch('ai_agent.requests.post')
    def test_max_attempts_defaults_to_two(self, mock_post):
        """
        Test that default max_attempts is 2 (1 initial + 1 retry).
        
        This verifies the default behavior matches the documented expectation.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'test response'}
        mock_post.return_value = mock_response

        # Call without specifying max_attempts
        result = call_ollama("test prompt")

        assert result == 'test response'
        # Should be called once on first attempt
        assert mock_post.call_count == 1

    @patch('ai_agent.requests.post')
    def test_max_attempts_two_retries_once_on_failure(self, mock_post):
        """
        Test that max_attempts=2 means 1 initial + 1 retry.
        
        Simulates failure on first attempt, success on second.
        """
        from requests.exceptions import ConnectionError
        
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'success'}
        
        mock_post.side_effect = [
            ConnectionError("Connection error"),  # First attempt fails
            mock_response  # Second attempt succeeds
        ]

        result = call_ollama("test prompt", max_attempts=2)

        assert result == 'success'
        assert mock_post.call_count == 2  # Called twice

    @patch('ai_agent.requests.post')
    def test_max_attempts_three_retries_twice_on_failure(self, mock_post):
        """
        Test that max_attempts=3 means 1 initial + 2 retries.
        
        Simulates failure on first two attempts, success on third.
        """
        from requests.exceptions import ConnectionError
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'success'}
        
        mock_post.side_effect = [
            ConnectionError("Connection error"),  # First attempt fails
            ConnectionError("Connection error"),  # Second attempt fails
            mock_response  # Third attempt succeeds
        ]

        result = call_ollama("test prompt", max_attempts=3)

        assert result == 'success'
        assert mock_post.call_count == 3  # Called three times

    @patch('ai_agent.requests.post')
    def test_max_attempts_exhausted_returns_none(self, mock_post):
        """
        Test that None is returned when all attempts fail.
        """
        from requests.exceptions import ConnectionError
        
        mock_post.side_effect = ConnectionError("Connection error")

        result = call_ollama("test prompt", max_attempts=2)

        assert result is None
        assert mock_post.call_count == 2  # All attempts exhausted

    @patch('ai_agent.requests.post')
    def test_http_error_retries(self, mock_post):
        """
        Test that HTTP errors also trigger retry logic.
        """
        from requests.exceptions import HTTPError
        
        # First call returns 503, second returns 200
        mock_response_503 = MagicMock()
        mock_response_503.status_code = 503
        mock_response_503.raise_for_status.side_effect = HTTPError("503 Service Unavailable")
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'response': 'success'}
        
        mock_post.side_effect = [mock_response_503, mock_response_200]

        result = call_ollama("test prompt", max_attempts=2)

        assert result == 'success'
        assert mock_post.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
