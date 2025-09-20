"""Unit tests for MCP resource endpoints.

This module contains tests for the FastMCP resource endpoints that expose data
through the MCP protocol, including listing all persons, listing all traits,
and retrieving individual person information.
"""
import pytest
from src.traits_matcher_server import list_persons_resource, list_traits_resource, get_person_resource, create_person_tool
from src.daos import MCPPersonDAO, MCPTraitDAO, get_db_connection
from src.models import PersonModel, TraitModel, Personality
import json
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
async def test_list_persons_resource(person_dao):
    await create_person_tool(name="John Doe")
    result = await list_persons_resource()
    persons = json.loads(result)
    assert len(persons) > 0
    assert persons[0]['name'] == "John Doe"

@pytest.mark.asyncio
async def test_list_traits_resource(trait_dao):
    personality = Personality(friendliness=8.0, dominance=2.0)
    trait_dao.add_trait("friendly", personality)
    result = await list_traits_resource()
    traits = json.loads(result)
    assert len(traits) > 0
    assert traits[0]['trait'] == "friendly"

@pytest.mark.asyncio
async def test_get_person_resource(person_dao):
    await create_person_tool(name="John Doe")
    result = await get_person_resource(name="John Doe")
    person = json.loads(result)
    assert person[0]['name'] == "John Doe"