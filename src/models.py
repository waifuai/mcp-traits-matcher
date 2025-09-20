"""Data models for the MCP Traits Matcher project."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class PersonModel(BaseModel):
    """Represents a person."""
    name: str = Field(description="The person's name.")
    friendliness: float = Field(ge=-10, le=10, description="The person's friendliness score (-10 to 10).")
    dominance: float = Field(ge=-10, le=10, description="The person's dominance score (-10 to 10).")


class TraitModel(BaseModel):
    """Represents a personality trait."""
    trait: str = Field(description="The name of the trait.")
    friendliness: float = Field(ge=-10, le=10, description="The friendliness score of the trait (-10 to 10).")
    dominance: float = Field(ge=-10, le=10, description="The dominance score of the trait (-10 to 10).")


class Personality(BaseModel):
    """Represents a personality profile."""
    friendliness: float
    dominance: float


class CreateTraitRequest(BaseModel):
    """Request model for creating a trait."""
    name: str = Field(description="The name of the trait.")
    friendliness: float = Field(ge=-10, le=10, description="Friendliness score (-10 to 10).")
    dominance: float = Field(ge=-10, le=10, description="Dominance score (-10 to 10).")


class AddDescriptionRequest(BaseModel):
    """Request model for adding a description."""
    name: str = Field(description="The person's name.")
    description: str = Field(description="Description to analyze.", max_length=1000)


class FindMatchesRequest(BaseModel):
    """Request model for finding matches."""
    company_name: str = Field(description="Name of the company.")
    job_description: str = Field(description="Description of the job/role.", max_length=1000)