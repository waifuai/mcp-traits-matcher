"""Main server implementation for the MCP Traits Matcher.

This module contains the FastMCP server setup, tool definitions, and resource endpoints
for personality analysis and matching. It provides the core functionality for creating
persons, managing traits, updating personalities based on descriptions, and finding
matches between people and job descriptions using Euclidean distance calculations.
"""
import json
import logging
import os
from scipy.spatial import distance

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, List

from .models import (
    PersonModel, TraitModel, Personality,
    CreateTraitRequest, AddDescriptionRequest, FindMatchesRequest
)
from .daos import MCPPersonDAO, MCPTraitDAO, DatabaseError

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- FastMCP Server Setup ---
mcp = FastMCP(
    "PersonalityAnalysisServer",
    description="Provides tools and resources for personality analysis and matching.",
    dependencies=[
        "scipy",
        "pydantic>=2.7.2,<3.0.0",
        "python-dotenv"
    ],
)

# Global DAO instances for better performance
person_dao = MCPPersonDAO()
trait_dao = MCPTraitDAO()

# --- Tools ---

@mcp.tool(name="create_person", description="Creates a new person with the given name.")
async def create_person_tool(name: str) -> str:
    """Creates a new person."""
    try:
        # Input validation
        if not name or not name.strip():
            raise ValueError("Person name cannot be empty")
        if len(name) > 100:
            raise ValueError("Person name too long (max 100 characters)")

        if person_dao.get_person(name):
            raise ValueError(f"Person '{name}' already exists.")
        person_dao.add_person(name)
        logger.info(f"Created person: {name}")
        return f"Person '{name}' created."
    except DatabaseError as e:
        logger.error(f"Database error creating person '{name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating person '{name}': {e}")
        raise

@mcp.tool(name="add_description", description="Adds a description to a person, updating their personality.")
async def add_description_tool(request: AddDescriptionRequest) -> str:
    """Adds a description to a person and updates their personality based on the traits in the description."""
    try:
        person = person_dao.get_person(request.name)
        if not person:
            raise ValueError(f"Person '{request.name}' not found.")

        words = request.description.lower().split()
        updated = False

        for word in words:
            if len(word) < 2:  # Skip very short words
                continue
            trait = trait_dao.get_trait(word)
            if trait:
                # Update person's personality using weighted average
                n_friendliness = person['n_friendliness']
                n_dominance = person['n_dominance']
                new_friendliness = ((person['friendliness'] * n_friendliness) + trait.friendliness) / (n_friendliness + 1)
                new_dominance = ((person['dominance'] * n_dominance) + trait.dominance) / (n_dominance + 1)
                person_dao.update_personality(request.name, Personality(friendliness=new_friendliness, dominance=new_dominance), n_friendliness + 1, n_dominance + 1)
                updated = True

        if not updated:
            logger.warning(f"No traits found in description for person '{request.name}'")

        logger.info(f"Added description to person: {request.name}")
        return f"Description added to person '{request.name}'."
    except DatabaseError as e:
        logger.error(f"Database error adding description to '{request.name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error adding description to '{request.name}': {e}")
        raise

@mcp.tool(name="create_trait", description="Creates a new personality trait.")
async def create_trait_tool(request: CreateTraitRequest) -> str:
    """Creates a new personality trait."""
    try:
        if trait_dao.get_trait(request.name):
            raise ValueError(f"Trait with name '{request.name}' already exists")
        trait_dao.add_trait(request.name, Personality(friendliness=request.friendliness, dominance=request.dominance))
        logger.info(f"Created trait: {request.name}")
        return f"Trait '{request.name}' created with friendliness: {request.friendliness}, dominance: {request.dominance}."
    except DatabaseError as e:
        logger.error(f"Database error creating trait '{request.name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating trait '{request.name}': {e}")
        raise

@mcp.tool(name="find_matches", description="Finds people matching a company's job description.")
async def find_matches_tool(request: FindMatchesRequest) -> List[str]:
    """Finds people matching a company's job description."""
    try:
        # Analyze job description to determine trait weights
        words = request.job_description.lower().split()
        trait_weights = {}
        for word in words:
            if len(word) < 2:  # Skip very short words
                continue
            trait = trait_dao.get_trait(word)
            if trait:
                trait_weights[word] = 1.0  # Assign weight 1.0 for valid traits

        # Calculate target personality (weighted average)
        if not trait_weights:
            target_personality = Personality(0.0, 0.0)  # Default if no traits found
            logger.info(f"No traits found in job description for '{request.company_name}'")
        else:
            avg_friendliness = sum(trait_dao.get_trait(trait).friendliness * weight for trait, weight in trait_weights.items()) / sum(trait_weights.values())
            avg_dominance = sum(trait_dao.get_trait(trait).dominance * weight for trait, weight in trait_weights.items()) / sum(trait_weights.values())
            target_personality = Personality(friendliness=avg_friendliness, dominance=avg_dominance)
            logger.info(f"Calculated target personality for '{request.company_name}': friendliness={avg_friendliness:.2f}, dominance={avg_dominance:.2f}")

        # Find people and calculate distances
        persons = person_dao.get_all()
        if not persons:
            logger.info("No persons found in database")
            return ["No persons found in database"]

        distances = []
        for person in persons:
            personality = Personality(friendliness=person['friendliness'], dominance=person['dominance'])
            dist = distance.euclidean(
                (personality.friendliness, personality.dominance),
                (target_personality.friendliness, target_personality.dominance)
            )
            distances.append((person['person'], dist))  # Use 'person' key for name

        # Sort by distance and return names
        matches = [name for name, dist in sorted(distances, key=lambda x: x[1])]
        logger.info(f"Found {len(matches)} matches for '{request.company_name}'")

        if not matches:
            return ["No matching persons were found"]
        return matches
    except DatabaseError as e:
        logger.error(f"Database error finding matches for '{request.company_name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error finding matches for '{request.company_name}': {e}")
        raise

# --- Resources ---

@mcp.resource("persons://all")
async def list_persons_resource() -> str:
    """Lists all persons in the database."""
    try:
        persons_data = person_dao.get_all()
        # Map 'person' key from DB to 'name' for the model
        persons_models = [PersonModel(name=p['person'], friendliness=p['friendliness'], dominance=p['dominance']) for p in persons_data]
        logger.debug(f"Retrieved {len(persons_models)} persons for resource")
        return json.dumps([p.model_dump() for p in persons_models])
    except DatabaseError as e:
        logger.error(f"Database error listing persons: {e}")
        return json.dumps({"error": "Database error occurred"})
    except Exception as e:
        logger.error(f"Unexpected error listing persons: {e}")
        return json.dumps({"error": "Internal server error"})

@mcp.resource("traits://all")
async def list_traits_resource() -> str:
    """Lists all available personality traits."""
    try:
        traits = trait_dao.get_all_traits()
        logger.debug(f"Retrieved {len(traits)} traits for resource")
        return json.dumps([TraitModel(**t).model_dump() for t in traits])
    except DatabaseError as e:
        logger.error(f"Database error listing traits: {e}")
        return json.dumps({"error": "Database error occurred"})
    except Exception as e:
        logger.error(f"Unexpected error listing traits: {e}")
        return json.dumps({"error": "Internal server error"})

@mcp.resource("persons://{name}")
async def get_person_resource(name: str) -> str:
    """Gets a person by their name."""
    try:
        person_data = person_dao.get_person(name)
        if not person_data:
            logger.warning(f"Person '{name}' not found")
            return json.dumps({"error": f"Person '{name}' not found"})
        # Map 'person' key from DB to 'name' for the model
        person_model = PersonModel(name=person_data['person'], friendliness=person_data['friendliness'], dominance=person_data['dominance'])
        logger.debug(f"Retrieved person: {name}")
        return json.dumps([person_model.model_dump()])
    except DatabaseError as e:
        logger.error(f"Database error getting person '{name}': {e}")
        return json.dumps({"error": "Database error occurred"})
    except Exception as e:
        logger.error(f"Unexpected error getting person '{name}': {e}")
        return json.dumps({"error": "Internal server error"})

if __name__ == "__main__":
    mcp.run()