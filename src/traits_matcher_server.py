import json
import sqlite3
from scipy.spatial import distance

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from typing import Annotated, List, Any, Optional, Dict

# --- Data Models (Pydantic) ---

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

# --- Database Connection ---

def get_db_connection(db_name: str):
    """Gets a database connection."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

# --- DAOs ---

class MCPPersonDAO:
    """Data Access Object for Person-related database operations."""
    def __init__(self):
        self.db_name = 'mcp_persons.db'
        self.create_tables()

    def create_tables(self):
        """Creates the persons table if it doesn't exist."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS persons (
                    person TEXT PRIMARY KEY,
                    friendliness REAL,
                    dominance REAL,
                    n_friendliness INTEGER,
                    n_dominance INTEGER
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_friendliness ON persons(friendliness)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dominance ON persons(dominance)')
            conn.commit()

    def get_all(self) -> List[Dict]:
        """Retrieves all persons from the database."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM persons')
            persons = [dict(row) for row in cursor.fetchall()]  # Convert rows to dictionaries
            return persons

    def get_person(self, name: str) -> Optional[Dict]:
        """Retrieves a person by their name."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM persons WHERE person=?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_personality(self, name: str, personality: Personality,
                         n_friendliness: int, n_dominance: int):
        """Updates a person's personality in the database."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE persons 
                SET friendliness=?, dominance=?, n_friendliness=?, n_dominance=?
                WHERE person=?
            ''', (personality.friendliness, personality.dominance,
                 n_friendliness, n_dominance, name))
            conn.commit()

    def add_person(self, name: str):
        """Adds a new person to the database with default values."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO persons (person, friendliness, dominance, n_friendliness, n_dominance) VALUES (?, ?, ?, ?, ?)',
                (name, 0.0, 0.0, 0, 0)  # Initialize with default values
            )
            conn.commit()


class MCPTraitDAO:
    """Data Access Object for Trait-related database operations."""
    def __init__(self):
        self.db_name = 'mcp_traits.db'
        self.create_tables()

    def create_tables(self):
        """Creates the traits table if it doesn't exist."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traits (
                    trait TEXT PRIMARY KEY,
                    friendliness REAL,
                    dominance REAL
                )
            ''')
            conn.commit()

    def get_all_traits(self) -> List[Dict]:
        """Retrieves all traits from the database."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT trait, friendliness, dominance FROM traits')
            traits = [dict(row) for row in cursor.fetchall()]  # Convert rows to dictionaries
            return traits

    def get_trait(self, name: str) -> Optional[Personality]:
        """Retrieves a trait by its name."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM traits WHERE trait=?', (name,))
            row = cursor.fetchone()
            if row is None:
                return None
            return Personality(friendliness=row['friendliness'], dominance=row['dominance'])

    def add_trait(self, name: str, personality: Personality):
        """Adds a new trait to the database."""
        with get_db_connection(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO traits VALUES (?, ?, ?)',
                (name, personality.friendliness, personality.dominance)
            )
            conn.commit()

# --- FastMCP Server Setup ---
mcp = FastMCP(
    "PersonalityAnalysisServer",
    description="Provides tools and resources for personality analysis and matching.",
    dependencies=[
        "scipy",
        "pydantic>=2.7.2,<3.0.0"
    ],
)

# --- Tools ---

@mcp.tool(name="create_person", description="Creates a new person with the given name.")
async def create_person_tool(name: str) -> str:
    """Creates a new person."""
    person_dao = MCPPersonDAO()
    if person_dao.get_person(name):
        raise ValueError(f"Person '{name}' already exists.")
    person_dao.add_person(name)
    return f"Person '{name}' created."

@mcp.tool(name="add_description", description="Adds a description to a person, updating their personality.")
async def add_description_tool(
    name: str,
    description: str,
) -> str:
    """Adds a description to a person and updates their personality based on the traits in the description."""
    person_dao = MCPPersonDAO()
    person = person_dao.get_person(name)
    if not person:
        raise ValueError(f"Person '{name}' not found.")

    trait_dao = MCPTraitDAO()
    words = description.lower().split()
    for word in words:
        trait = trait_dao.get_trait(word)
        if trait:
            # Update person's personality using weighted average
            n_friendliness = person['n_friendliness']
            n_dominance = person['n_dominance']
            new_friendliness = ((person['friendliness'] * n_friendliness) + trait.friendliness) / (n_friendliness + 1)
            new_dominance = ((person['dominance'] * n_dominance) + trait.dominance) / (n_dominance + 1)
            person_dao.update_personality(name, Personality(friendliness=new_friendliness, dominance=new_dominance), n_friendliness + 1, n_dominance + 1)

    return f"Description added to person '{name}'."

@mcp.tool(name="create_trait", description="Creates a new personality trait.")
async def create_trait_tool(
    name: str,
    friendliness: Annotated[float, Field(ge=-10, le=10, description="Friendliness score (-10 to 10).")],
    dominance: Annotated[float, Field(ge=-10, le=10, description="Dominance score (-10 to 10).")]
) -> str:
    """Creates a new personality trait."""
    trait_dao = MCPTraitDAO()
    if trait_dao.get_trait(name):
        raise ValueError(f"Trait with name '{name}' already exists")
    trait_dao.add_trait(name, Personality(friendliness=friendliness, dominance=dominance))
    return f"Trait '{name}' created with friendliness: {friendliness}, dominance: {dominance}."

@mcp.tool(name="find_matches", description="Finds people matching a company's job description.")
async def find_matches_tool(
    company_name: str = Field(description="Name of the company."),
    job_description: str = Field(description="Description of the job/role.")
) -> List[str]:
    """Finds people matching a company's job description."""
    person_dao = MCPPersonDAO()
    trait_dao = MCPTraitDAO()

    # Analyze job description to determine trait weights
    words = job_description.lower().split()
    trait_weights = {}
    for word in words:
        trait = trait_dao.get_trait(word)
        if trait:
            trait_weights[word] = 1.0  # Assign weight 1.0 for valid traits

    # Calculate target personality (weighted average)
    if not trait_weights:
        target_personality = Personality(0.0, 0.0)  # Default if no traits found
    else:
        avg_friendliness = sum(trait_dao.get_trait(trait).friendliness * weight for trait, weight in trait_weights.items()) / sum(trait_weights.values())
        avg_dominance = sum(trait_dao.get_trait(trait).dominance * weight for trait, weight in trait_weights.items()) / sum(trait_weights.values())
        target_personality = Personality(friendliness=avg_friendliness, dominance=avg_dominance)

    # Find people and calculate distances
    persons = person_dao.get_all()
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
    if not matches:
        return ["No matching persons were found"]
    return matches

# --- Resources ---

@mcp.resource("persons://all")
async def list_persons_resource() -> str:
    """Lists all persons in the database."""
    person_dao = MCPPersonDAO()
    persons_data = person_dao.get_all()
    # Map 'person' key from DB to 'name' for the model
    persons_models = [PersonModel(name=p['person'], friendliness=p['friendliness'], dominance=p['dominance']) for p in persons_data]
    return json.dumps([p.model_dump() for p in persons_models])

@mcp.resource("traits://all")
async def list_traits_resource() -> str:
    """Lists all available personality traits."""
    trait_dao = MCPTraitDAO()
    traits = trait_dao.get_all_traits()
    return json.dumps([TraitModel(**t).model_dump() for t in traits])

@mcp.resource("persons://{name}")
async def get_person_resource(name: str) -> str:
    """Gets a person by their name."""
    person_dao = MCPPersonDAO()
    person_data = person_dao.get_person(name)
    if not person_data:
        raise ValueError(f"Person '{name}' not found")
    # Map 'person' key from DB to 'name' for the model
    person_model = PersonModel(name=person_data['person'], friendliness=person_data['friendliness'], dominance=person_data['dominance'])
    return json.dumps([person_model.model_dump()])

if __name__ == "__main__":
    mcp.run()