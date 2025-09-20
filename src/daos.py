"""Data Access Objects for database operations."""

import sqlite3
import logging
import os
from typing import List, Dict, Optional
from contextlib import contextmanager

from .models import Personality

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
PERSONS_DB = os.getenv('MCP_PERSONS_DB', 'mcp_persons.db')
TRAITS_DB = os.getenv('MCP_TRAITS_DB', 'mcp_traits.db')


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


@contextmanager
def get_db_connection(db_name: str):
    """Context manager for database connections with error handling."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row  # Access columns by name
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error for {db_name}: {e}")
        raise DatabaseError(f"Failed to connect to database {db_name}: {e}")
    finally:
        if conn:
            conn.close()


class MCPPersonDAO:
    """Data Access Object for Person-related database operations."""

    def __init__(self):
        self.db_name = PERSONS_DB
        self.create_tables()

    def create_tables(self):
        """Creates the persons table if it doesn't exist."""
        try:
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
                logger.info(f"Persons table created successfully in {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to create persons table: {e}")
            raise DatabaseError(f"Failed to create persons table: {e}")

    def get_all(self) -> List[Dict]:
        """Retrieves all persons from the database."""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM persons')
                persons = [dict(row) for row in cursor.fetchall()]
                logger.debug(f"Retrieved {len(persons)} persons from database")
                return persons
        except Exception as e:
            logger.error(f"Failed to retrieve all persons: {e}")
            raise DatabaseError(f"Failed to retrieve persons: {e}")

    def get_person(self, name: str) -> Optional[Dict]:
        """Retrieves a person by their name."""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM persons WHERE person=?', (name,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to retrieve person '{name}': {e}")
            raise DatabaseError(f"Failed to retrieve person '{name}': {e}")

    def update_personality(self, name: str, personality: Personality,
                         n_friendliness: int, n_dominance: int):
        """Updates a person's personality in the database."""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE persons
                    SET friendliness=?, dominance=?, n_friendliness=?, n_dominance=?
                    WHERE person=?
                ''', (personality.friendliness, personality.dominance,
                     n_friendliness, n_dominance, name))
                if cursor.rowcount == 0:
                    raise DatabaseError(f"Person '{name}' not found for update")
                conn.commit()
                logger.info(f"Updated personality for person '{name}'")
        except Exception as e:
            logger.error(f"Failed to update personality for '{name}': {e}")
            raise DatabaseError(f"Failed to update personality for '{name}': {e}")

    def add_person(self, name: str):
        """Adds a new person to the database with default values."""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO persons (person, friendliness, dominance, n_friendliness, n_dominance) VALUES (?, ?, ?, ?, ?)',
                    (name, 0.0, 0.0, 0, 0)
                )
                conn.commit()
                logger.info(f"Added new person '{name}' to database")
        except sqlite3.IntegrityError:
            logger.warning(f"Person '{name}' already exists")
            raise DatabaseError(f"Person '{name}' already exists")
        except Exception as e:
            logger.error(f"Failed to add person '{name}': {e}")
            raise DatabaseError(f"Failed to add person '{name}': {e}")


class MCPTraitDAO:
    """Data Access Object for Trait-related database operations."""

    def __init__(self):
        self.db_name = TRAITS_DB
        self.create_tables()

    def create_tables(self):
        """Creates the traits table if it doesn't exist."""
        try:
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
                logger.info(f"Traits table created successfully in {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to create traits table: {e}")
            raise DatabaseError(f"Failed to create traits table: {e}")

    def get_all_traits(self) -> List[Dict]:
        """Retrieves all traits from the database."""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT trait, friendliness, dominance FROM traits')
                traits = [dict(row) for row in cursor.fetchall()]
                logger.debug(f"Retrieved {len(traits)} traits from database")
                return traits
        except Exception as e:
            logger.error(f"Failed to retrieve all traits: {e}")
            raise DatabaseError(f"Failed to retrieve traits: {e}")

    def get_trait(self, name: str) -> Optional[Personality]:
        """Retrieves a trait by its name."""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM traits WHERE trait=?', (name,))
                row = cursor.fetchone()
                if row is None:
                    return None
                return Personality(friendliness=row['friendliness'], dominance=row['dominance'])
        except Exception as e:
            logger.error(f"Failed to retrieve trait '{name}': {e}")
            raise DatabaseError(f"Failed to retrieve trait '{name}': {e}")

    def add_trait(self, name: str, personality: Personality):
        """Adds a new trait to the database."""
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO traits VALUES (?, ?, ?)',
                    (name, personality.friendliness, personality.dominance)
                )
                conn.commit()
                logger.info(f"Added new trait '{name}' to database")
        except sqlite3.IntegrityError:
            logger.warning(f"Trait '{name}' already exists")
            raise DatabaseError(f"Trait '{name}' already exists")
        except Exception as e:
            logger.error(f"Failed to add trait '{name}': {e}")
            raise DatabaseError(f"Failed to add trait '{name}': {e}")