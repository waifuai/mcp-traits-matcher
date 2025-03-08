import pytest
from src.traits_matcher_server import PersonModel, TraitModel

def test_person_model_valid_data():
    person = PersonModel(name="John Doe", friendliness=5.0, dominance=2.0)
    assert person.name == "John Doe"
    assert person.friendliness == 5.0
    assert person.dominance == 2.0

def test_person_model_invalid_data():
    with pytest.raises(ValueError):
        PersonModel(name="John Doe", friendliness=15.0, dominance=2.0)

def test_trait_model_valid_data():
    trait = TraitModel(trait="friendly", friendliness=8.0, dominance=2.0)
    assert trait.trait == "friendly"
    assert trait.friendliness == 8.0
    assert trait.dominance == 2.0

def test_trait_model_invalid_data():
    with pytest.raises(ValueError):
        TraitModel(trait="friendly", friendliness=15.0, dominance=2.0)