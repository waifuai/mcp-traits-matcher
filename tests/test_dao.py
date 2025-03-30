import pytest
from src.traits_matcher_server import MCPPersonDAO, MCPTraitDAO, Personality
from src.traits_matcher_server import get_db_connection, Personality
import sqlite3

@pytest.fixture
def person_dao():
    dao = MCPPersonDAO()
    # Ensure a clean database for testing
    conn = sqlite3.connect(dao.db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM persons")
    conn.commit()
    conn.close()
    return dao

@pytest.fixture
def trait_dao():
    dao = MCPTraitDAO()
    # Ensure a clean database for testing
    conn = sqlite3.connect(dao.db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM traits")
    conn.commit()
    conn.close()
    return dao

def test_person_dao_add_and_get_person(person_dao):
    person_dao.add_person("John Doe")
    person = person_dao.get_person("John Doe")
    assert person is not None
    assert person['person'] == "John Doe"

def test_person_dao_update_personality(person_dao):
    person_dao.add_person("John Doe")
    personality = Personality(friendliness=7.0, dominance=3.0)
    person_dao.update_personality("John Doe", personality, 5, 2)
    person = person_dao.get_person("John Doe")
    assert person['friendliness'] == 7.0
    assert person['dominance'] == 3.0

def test_trait_dao_add_and_get_trait(trait_dao):
    personality = Personality(friendliness=8.0, dominance=2.0)
    trait_dao.add_trait("friendly", personality)
    trait = trait_dao.get_trait("friendly")
    assert trait is not None
    assert trait.friendliness == 8.0
    assert trait.dominance == 2.0