import pytest
from pydantic import ValidationError
from src.models import (
    PersonModel, TraitModel, Personality,
    CreateTraitRequest, AddDescriptionRequest, FindMatchesRequest
)


def test_person_model_valid_data():
    person = PersonModel(name="John Doe", friendliness=5.0, dominance=2.0)
    assert person.name == "John Doe"
    assert person.friendliness == 5.0
    assert person.dominance == 2.0


def test_person_model_boundary_values():
    """Test person model with boundary values."""
    # Test minimum values
    person = PersonModel(name="Test", friendliness=-10.0, dominance=-10.0)
    assert person.friendliness == -10.0
    assert person.dominance == -10.0

    # Test maximum values
    person = PersonModel(name="Test", friendliness=10.0, dominance=10.0)
    assert person.friendliness == 10.0
    assert person.dominance == 10.0


def test_person_model_invalid_data():
    # Test friendliness too high
    with pytest.raises(ValidationError, match="friendliness"):
        PersonModel(name="John Doe", friendliness=15.0, dominance=2.0)

    # Test friendliness too low
    with pytest.raises(ValidationError, match="friendliness"):
        PersonModel(name="John Doe", friendliness=-15.0, dominance=2.0)

    # Test dominance too high
    with pytest.raises(ValidationError, match="dominance"):
        PersonModel(name="John Doe", friendliness=5.0, dominance=15.0)

    # Test dominance too low
    with pytest.raises(ValidationError, match="dominance"):
        PersonModel(name="John Doe", friendliness=5.0, dominance=-15.0)


def test_person_model_edge_cases():
    """Test person model with edge cases."""
    # Empty name should be valid (though not recommended)
    person = PersonModel(name="", friendliness=0.0, dominance=0.0)
    assert person.name == ""

    # Very long name
    long_name = "A" * 1000
    person = PersonModel(name=long_name, friendliness=0.0, dominance=0.0)
    assert person.name == long_name


def test_trait_model_valid_data():
    trait = TraitModel(trait="friendly", friendliness=8.0, dominance=2.0)
    assert trait.trait == "friendly"
    assert trait.friendliness == 8.0
    assert trait.dominance == 2.0


def test_trait_model_boundary_values():
    """Test trait model with boundary values."""
    # Test minimum values
    trait = TraitModel(trait="shy", friendliness=-10.0, dominance=-10.0)
    assert trait.friendliness == -10.0
    assert trait.dominance == -10.0

    # Test maximum values
    trait = TraitModel(trait="extrovert", friendliness=10.0, dominance=10.0)
    assert trait.friendliness == 10.0
    assert trait.dominance == 10.0


def test_trait_model_invalid_data():
    # Test friendliness too high
    with pytest.raises(ValidationError, match="friendliness"):
        TraitModel(trait="friendly", friendliness=15.0, dominance=2.0)

    # Test dominance too low
    with pytest.raises(ValidationError, match="dominance"):
        TraitModel(trait="friendly", friendliness=8.0, dominance=-15.0)


def test_personality_model():
    """Test Personality model."""
    personality = Personality(friendliness=5.0, dominance=3.0)
    assert personality.friendliness == 5.0
    assert personality.dominance == 3.0


def test_create_trait_request_valid():
    """Test CreateTraitRequest model."""
    request = CreateTraitRequest(name="friendly", friendliness=8.0, dominance=2.0)
    assert request.name == "friendly"
    assert request.friendliness == 8.0
    assert request.dominance == 2.0


def test_create_trait_request_invalid():
    """Test CreateTraitRequest with invalid data."""
    with pytest.raises(ValidationError):
        CreateTraitRequest(name="friendly", friendliness=15.0, dominance=2.0)


def test_add_description_request_valid():
    """Test AddDescriptionRequest model."""
    request = AddDescriptionRequest(name="John Doe", description="friendly and outgoing")
    assert request.name == "John Doe"
    assert request.description == "friendly and outgoing"


def test_add_description_request_length_limit():
    """Test AddDescriptionRequest with description that exceeds length limit."""
    long_description = "A" * 1001  # Exceeds max_length=1000
    with pytest.raises(ValidationError, match="description"):
        AddDescriptionRequest(name="John Doe", description=long_description)


def test_find_matches_request_valid():
    """Test FindMatchesRequest model."""
    request = FindMatchesRequest(
        company_name="Acme Corp",
        job_description="Looking for friendly candidates"
    )
    assert request.company_name == "Acme Corp"
    assert request.job_description == "Looking for friendly candidates"


def test_find_matches_request_length_limit():
    """Test FindMatchesRequest with job description that exceeds length limit."""
    long_description = "A" * 1001  # Exceeds max_length=1000
    with pytest.raises(ValidationError, match="job_description"):
        FindMatchesRequest(company_name="Acme Corp", job_description=long_description)


def test_models_serialization():
    """Test that models can be properly serialized to dictionaries."""
    person = PersonModel(name="John Doe", friendliness=5.0, dominance=2.0)
    data = person.model_dump()
    assert data == {
        "name": "John Doe",
        "friendliness": 5.0,
        "dominance": 2.0
    }

    # Test that we can recreate the model from the data
    person2 = PersonModel(**data)
    assert person2 == person

def test_trait_model_valid_data():
    trait = TraitModel(trait="friendly", friendliness=8.0, dominance=2.0)
    assert trait.trait == "friendly"
    assert trait.friendliness == 8.0
    assert trait.dominance == 2.0

def test_trait_model_invalid_data():
    with pytest.raises(ValidationError):
        TraitModel(trait="friendly", friendliness=15.0, dominance=2.0)