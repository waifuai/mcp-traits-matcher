import pytest
import os
from unittest.mock import patch

from src.daos import MCPPersonDAO, MCPTraitDAO, DatabaseError
from src.models import Personality


def test_person_dao_create_tables(person_dao):
    """Test that tables are created successfully."""
    # If we can add a person, tables were created
    person_dao.add_person("Test Person")
    person = person_dao.get_person("Test Person")
    assert person is not None


def test_person_dao_add_and_get_person(person_dao):
    person_dao.add_person("John Doe")
    person = person_dao.get_person("John Doe")
    assert person is not None
    assert person['person'] == "John Doe"
    assert person['friendliness'] == 0.0
    assert person['dominance'] == 0.0
    assert person['n_friendliness'] == 0
    assert person['n_dominance'] == 0


def test_person_dao_add_duplicate_person(person_dao):
    """Test adding a person that already exists raises an error."""
    person_dao.add_person("John Doe")
    with pytest.raises(DatabaseError, match="already exists"):
        person_dao.add_person("John Doe")


def test_person_dao_get_nonexistent_person(person_dao):
    """Test getting a person that doesn't exist."""
    person = person_dao.get_person("Nonexistent Person")
    assert person is None


def test_person_dao_update_personality(person_dao):
    person_dao.add_person("John Doe")
    personality = Personality(friendliness=7.0, dominance=3.0)
    person_dao.update_personality("John Doe", personality, 5, 2)
    person = person_dao.get_person("John Doe")
    assert person['friendliness'] == 7.0
    assert person['dominance'] == 3.0
    assert person['n_friendliness'] == 5
    assert person['n_dominance'] == 2


def test_person_dao_update_nonexistent_person(person_dao):
    """Test updating a person that doesn't exist raises an error."""
    personality = Personality(friendliness=7.0, dominance=3.0)
    with pytest.raises(DatabaseError, match="not found"):
        person_dao.update_personality("Nonexistent Person", personality, 1, 1)


def test_person_dao_get_all_empty(person_dao):
    """Test getting all persons when database is empty."""
    persons = person_dao.get_all()
    assert persons == []


def test_person_dao_get_all_with_data(person_dao):
    """Test getting all persons with data."""
    person_dao.add_person("John Doe")
    person_dao.add_person("Jane Smith")
    persons = person_dao.get_all()
    assert len(persons) == 2
    names = [p['person'] for p in persons]
    assert "John Doe" in names
    assert "Jane Smith" in names


def test_trait_dao_create_tables(trait_dao):
    """Test that trait tables are created successfully."""
    # If we can add a trait, tables were created
    personality = Personality(friendliness=8.0, dominance=2.0)
    trait_dao.add_trait("friendly", personality)
    trait = trait_dao.get_trait("friendly")
    assert trait is not None


def test_trait_dao_add_and_get_trait(trait_dao):
    personality = Personality(friendliness=8.0, dominance=2.0)
    trait_dao.add_trait("friendly", personality)
    trait = trait_dao.get_trait("friendly")
    assert trait is not None
    assert trait.friendliness == 8.0
    assert trait.dominance == 2.0


def test_trait_dao_add_duplicate_trait(trait_dao):
    """Test adding a trait that already exists raises an error."""
    personality = Personality(friendliness=8.0, dominance=2.0)
    trait_dao.add_trait("friendly", personality)
    with pytest.raises(DatabaseError, match="already exists"):
        trait_dao.add_trait("friendly", personality)


def test_trait_dao_get_nonexistent_trait(trait_dao):
    """Test getting a trait that doesn't exist."""
    trait = trait_dao.get_trait("nonexistent")
    assert trait is None


def test_trait_dao_get_all_empty(trait_dao):
    """Test getting all traits when database is empty."""
    traits = trait_dao.get_all_traits()
    assert traits == []


def test_trait_dao_get_all_with_data(trait_dao):
    """Test getting all traits with data."""
    trait_dao.add_trait("friendly", Personality(friendliness=8.0, dominance=2.0))
    trait_dao.add_trait("dominant", Personality(friendliness=-2.0, dominance=9.0))
    traits = trait_dao.get_all_traits()
    assert len(traits) == 2
    trait_names = [t['trait'] for t in traits]
    assert "friendly" in trait_names
    assert "dominant" in trait_names


def test_database_error_on_corrupted_db(person_dao, temp_db_path):
    """Test that database errors are handled gracefully."""
    # Make the database file unreadable
    os.chmod(temp_db_path, 0o000)
    with pytest.raises(DatabaseError):
        person_dao.get_all()
    # Restore permissions for cleanup
    os.chmod(temp_db_path, 0o644)