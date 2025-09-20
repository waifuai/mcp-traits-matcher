"""Test configuration and fixtures for MCP Traits Matcher."""

import os
import tempfile
import pytest
import sqlite3
from unittest.mock import patch

from src.daos import MCPPersonDAO, MCPTraitDAO
from src.models import Personality


@pytest.fixture(scope="session")
def temp_db_dir():
    """Create a temporary directory for test databases."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup will be handled by pytest


@pytest.fixture
def person_dao(temp_db_dir):
    """Create a person DAO with temporary database."""
    db_path = os.path.join(temp_db_dir, "test_persons.db")
    with patch.dict(os.environ, {'MCP_PERSONS_DB': db_path}):
        dao = MCPPersonDAO()
        # Clean up any existing data (table is created by DAO constructor)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM persons WHERE 1=1")
        conn.commit()
        conn.close()
        return dao


@pytest.fixture
def trait_dao(temp_db_dir):
    """Create a trait DAO with temporary database."""
    db_path = os.path.join(temp_db_dir, "test_traits.db")
    with patch.dict(os.environ, {'MCP_TRAITS_DB': db_path}):
        dao = MCPTraitDAO()
        # Clean up any existing data (table is created by DAO constructor)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM traits WHERE 1=1")
        conn.commit()
        conn.close()
        return dao


@pytest.fixture
def sample_person(person_dao):
    """Create a sample person for testing."""
    person_dao.add_person("John Doe")
    return "John Doe"


@pytest.fixture
def sample_trait(trait_dao):
    """Create a sample trait for testing."""
    trait_dao.add_trait("friendly", Personality(friendliness=8.0, dominance=2.0))
    return "friendly"


@pytest.fixture
def populated_person_dao(person_dao, trait_dao):
    """Create a DAO with sample data for integration tests."""
    # Add some sample traits
    trait_dao.add_trait("friendly", Personality(friendliness=8.0, dominance=2.0))
    trait_dao.add_trait("dominant", Personality(friendliness=-2.0, dominance=9.0))
    trait_dao.add_trait("outgoing", Personality(friendliness=7.0, dominance=4.0))

    # Add some sample persons
    person_dao.add_person("John Doe")
    person_dao.add_person("Jane Smith")
    person_dao.add_person("Bob Johnson")

    # Update some personalities
    person_dao.update_personality("John Doe", Personality(friendliness=6.0, dominance=3.0), 1, 1)
    person_dao.update_personality("Jane Smith", Personality(friendliness=7.0, dominance=5.0), 1, 1)

    return person_dao, trait_dao


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)