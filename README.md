# MCP Traits Matcher

## Description

A personality analysis server built using the FastMCP framework. It provides tools and resources for personality analysis and matching.

## Features

*   Creates persons and traits.
*   Adds descriptions to persons, updating their personality based on traits.
*   Finds people matching a company's job description.
*   Exposes resources for listing persons and traits.

## Setup Instructions

### Prerequisites

*   Python 3.x
*   pip

### Installation

1.  Clone the repository.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate the virtual environment:
    *   Windows: `venv\Scripts\activate`
    *   Linux/macOS: `source venv/bin/activate`
4.  Install dependencies: `pip install --user -r requirements.txt`

### Database Setup

The server uses SQLite databases (`mcp_persons.db` and `mcp_traits.db`). These databases will be created automatically when the server is run.

## Usage Examples

### Creating a person

```python
mcp.create_person(name="John Doe")
```

### Adding a description to a person

```python
mcp.add_description(name="John Doe", description="friendly and dominant")
```

### Creating a trait

```python
mcp.create_trait(name="friendly", friendliness=8.0, dominance=2.0)
```

### Finding matches for a job description

```python
mcp.find_matches(company_name="Acme Corp", job_description="Looking for friendly and dominant candidates")
```

## API Documentation

### Resources

*   `persons://all`: Lists all persons.
*   `traits://all`: Lists all traits.
*   `persons://{name}`: Gets a person by their name.

### Tools

*   `create_person`: Creates a new person.
*   `add_description`: Adds a description to a person.
*   `create_trait`: Creates a new trait.
*   `find_matches`: Finds people matching a job description.

## Dependencies

*   `scipy`
*   `pydantic>=2.7.2,<3.0.0`
*   `fastmcp`

## License

MIT-0 License