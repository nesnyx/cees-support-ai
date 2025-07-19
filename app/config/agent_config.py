import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
AGENT_DB_CONFIG = {
    "PSQL_USERNAME": os.getenv("PSQL_USERNAME", "user_production"),
    "PSQL_PASSWORD": os.getenv("PSQL_PASSWORD", "kodecesar1234"), 
    "PSQL_HOST": os.getenv("PSQL_HOST", "arisbara.cloud"),
    "PSQL_PORT": os.getenv("PSQL_PORT", "3499"),
    "PSQL_DATABASE": os.getenv("PSQL_DATABASE", "cees_db"),
    "PSQL_SSLMODE": os.getenv("PSQL_SSLMODE", "prefer")
}

def get_db_connection_string():
    """Get database connection string"""
    return (
        f"postgres://{AGENT_DB_CONFIG['PSQL_USERNAME']}:{AGENT_DB_CONFIG['PSQL_PASSWORD']}"
        f"@{AGENT_DB_CONFIG['PSQL_HOST']}:{AGENT_DB_CONFIG['PSQL_PORT']}/{AGENT_DB_CONFIG['PSQL_DATABASE']}"
        f"?sslmode={AGENT_DB_CONFIG['PSQL_SSLMODE']}"
    )
