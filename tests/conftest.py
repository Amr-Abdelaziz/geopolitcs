"""Pytest configuration ensuring unit tests run safely and deterministically
without burning live API credits.
"""
import os
import pytest

# Ensure tests run in mock mode to protect user credits
os.environ["MOCK_LLM"] = "1"
