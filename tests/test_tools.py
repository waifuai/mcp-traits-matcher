"""Unit tests for MCP tools functionality.

This module contains tests for the FastMCP tools that provide the core business
logic, including creating persons, adding descriptions, creating traits, and
finding matches between people and job descriptions.
"""
import pytest
from src.traits_matcher_server import create_person_tool, add_description_tool, create_trait_tool, find_matches_tool
from src.daos import MCPPersonDAO, MCPTraitDAO, get_db_connection
from src.models import Personality
import asyncio

@pytest.fixture
def person_dao():
    dao = MCPPersonDAO()
    # Ensure a clean database for testing
    conn = get_db_connection(dao.db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM persons")
    conn.commit()
    conn.close()
    return dao

@pytest.fixture
def trait_dao():
    dao = MCPTraitDAO()
    # Ensure a clean database for testing
    conn = get_db_connection(dao.db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM traits")
    conn.commit()
    conn.close()
    return dao

@pytest.mark.asyncio
async def test_create_person_tool(person_dao):
    result = await create_person_tool(name="John Doe")
    assert result == "Person 'John Doe' created."
    person = person_dao.get_person("John Doe")
    assert person is not None

@pytest.mark.asyncio
async def test_add_description_tool(person_dao, trait_dao):
    await create_person_tool(name="John Doe")
    personality = Personality(friendliness=8.0, dominance=2.0)
    trait_dao.add_trait("friendly", personality)
    result = await add_description_tool(name="John Doe", description="friendly")
    assert result == "Description added to person 'John Doe'."
    person = person_dao.get_person("John Doe")
    assert person['friendliness'] > 0
    assert person['dominance'] > 0

@pytest.mark.asyncio
async def test_create_trait_tool(trait_dao):
    result = await create_trait_tool(name="friendly", friendliness=8.0, dominance=2.0)
    assert "Trait 'friendly' created" in result
    trait = trait_dao.get_trait("friendly")
    assert trait is not None
    assert trait.friendliness == 8.0
    assert trait.dominance == 2.0

@pytest.mark.asyncio
async def test_find_matches_tool(person_dao, trait_dao):
    await create_person_tool(name="John Doe")
    personality = Personality(friendliness=8.0, dominance=2.0)
    trait_dao.add_trait("friendly", personality)
    await add_description_tool(name="John Doe", description="friendly")
    result = await find_matches_tool(company_name="Acme Corp", job_description="friendly")
    assert "John Doe" in result