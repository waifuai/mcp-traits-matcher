"""Integration tests for MCP Traits Matcher."""

import pytest
import json
from unittest.mock import patch

from src.traits_matcher_server import (
    create_person_tool, add_description_tool, create_trait_tool,
    find_matches_tool, list_persons_resource, list_traits_resource,
    get_person_resource
)
from src.models import Personality


@pytest.mark.asyncio
async def test_full_workflow_integration(populated_person_dao):
    """Test a complete workflow from creating traits to finding matches."""
    person_dao, trait_dao = populated_person_dao

    # Create a new trait
    result = await create_trait_tool(
        name="confident",
        friendliness=3.0,
        dominance=8.0
    )
    assert "Trait 'confident' created" in result

    # Create a new person
    result = await create_person_tool(name="Alice Cooper")
    assert result == "Person 'Alice Cooper' created."

    # Add description to update personality
    result = await add_description_tool(
        name="Alice Cooper",
        description="very confident and friendly"
    )
    assert result == "Description added to person 'Alice Cooper'."

    # Check that personality was updated
    person = person_dao.get_person("Alice Cooper")
    assert person['friendliness'] > 0  # Should be positive due to "friendly"
    assert person['dominance'] > 0    # Should be positive due to "confident"

    # Test finding matches
    result = await find_matches_tool(
        company_name="Tech Corp",
        job_description="Looking for confident and friendly people"
    )
    assert "Alice Cooper" in result

    # Test resource endpoints
    persons_result = await list_persons_resource()
    persons_data = json.loads(persons_result)
    assert len(persons_data) >= 4  # 3 original + Alice

    traits_result = await list_traits_resource()
    traits_data = json.loads(traits_result)
    assert len(traits_data) >= 4  # 3 original + confident

    person_result = await get_person_resource(name="Alice Cooper")
    person_data = json.loads(person_result)
    assert person_data[0]['name'] == "Alice Cooper"


@pytest.mark.asyncio
async def test_error_handling_integration(person_dao, trait_dao):
    """Test error handling across the application."""

    # Test creating person with empty name
    with pytest.raises(ValueError, match="Person name cannot be empty"):
        await create_person_tool(name="")

    # Test creating duplicate person
    await create_person_tool(name="Test Person")
    with pytest.raises(ValueError, match="already exists"):
        await create_person_tool(name="Test Person")

    # Test adding description to non-existent person
    with pytest.raises(ValueError, match="not found"):
        await add_description_tool(name="Nonexistent", description="friendly")

    # Test creating duplicate trait
    await create_trait_tool(name="test_trait", friendliness=5.0, dominance=3.0)
    with pytest.raises(ValueError, match="already exists"):
        await create_trait_tool(name="test_trait", friendliness=5.0, dominance=3.0)


@pytest.mark.asyncio
async def test_personality_update_workflow(person_dao, trait_dao):
    """Test the personality update workflow in detail."""
    # Create traits
    await create_trait_tool(name="extrovert", friendliness=9.0, dominance=6.0)
    await create_trait_tool(name="introvert", friendliness=-5.0, dominance=-3.0)

    # Create person
    await create_person_tool(name="Test Subject")

    # Add multiple descriptions to see personality evolution
    await add_description_tool(name="Test Subject", description="extrovert and friendly")
    person = person_dao.get_person("Test Subject")
    assert person['n_friendliness'] == 1
    assert person['n_dominance'] == 1

    # Add another description
    await add_description_tool(name="Test Subject", description="introvert tendencies")
    person = person_dao.get_person("Test Subject")
    assert person['n_friendliness'] == 2
    assert person['n_dominance'] == 2

    # Check that personality is an average
    # First update: extrovert (9.0, 6.0) -> person becomes (9.0, 6.0)
    # Second update: introvert (-5.0, -3.0) -> average = ((9.0 + (-5.0))/2, (6.0 + (-3.0))/2) = (2.0, 1.5)
    assert abs(person['friendliness'] - 2.0) < 0.01
    assert abs(person['dominance'] - 1.5) < 0.01


@pytest.mark.asyncio
async def test_matching_algorithm_integration(populated_person_dao):
    """Test the matching algorithm with various scenarios."""
    person_dao, trait_dao = populated_person_dao

    # Create specific traits for testing
    await create_trait_tool(name="analytical", friendliness=-1.0, dominance=2.0)
    await create_trait_tool(name="creative", friendliness=4.0, dominance=-2.0)

    # Create people with specific traits
    await create_person_tool(name="Data Scientist")
    await create_person_tool(name="Artist")

    # Update their personalities
    person_dao.update_personality("Data Scientist", Personality(friendliness=-1.0, dominance=2.0), 1, 1)
    person_dao.update_personality("Artist", Personality(friendliness=4.0, dominance=-2.0), 1, 1)

    # Test matching for analytical job
    matches = await find_matches_tool(
        company_name="Analytics Firm",
        job_description="Need analytical and precise person"
    )
    # Data Scientist should be a better match for analytical work
    assert matches[0] == "Data Scientist"

    # Test matching for creative job
    matches = await find_matches_tool(
        company_name="Design Studio",
        job_description="Looking for creative and artistic person"
    )
    # Artist should be a better match for creative work
    assert matches[0] == "Artist"


@pytest.mark.asyncio
async def test_resource_endpoints_integration(populated_person_dao):
    """Test that resource endpoints return correct data."""
    person_dao, trait_dao = populated_person_dao

    # Test persons resource
    result = await list_persons_resource()
    persons_data = json.loads(result)
    assert isinstance(persons_data, list)
    assert len(persons_data) >= 3

    # Verify structure
    for person in persons_data:
        assert 'name' in person
        assert 'friendliness' in person
        assert 'dominance' in person
        assert isinstance(person['friendliness'], (int, float))
        assert isinstance(person['dominance'], (int, float))

    # Test traits resource
    result = await list_traits_resource()
    traits_data = json.loads(result)
    assert isinstance(traits_data, list)
    assert len(traits_data) >= 3

    # Verify structure
    for trait in traits_data:
        assert 'trait' in trait
        assert 'friendliness' in trait
        assert 'dominance' in trait

    # Test individual person resource
    result = await get_person_resource(name="John Doe")
    person_data = json.loads(result)
    assert isinstance(person_data, list)
    assert len(person_data) == 1
    assert person_data[0]['name'] == "John Doe"