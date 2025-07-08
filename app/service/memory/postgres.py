
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


db_conn="postgresql://user_production:kodecesar1234@arisbara.cloud:3499/cees_db"

async def memory():
    async with AsyncConnectionPool(
    conninfo=db_conn,
    max_size=20,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
    }
    ) as pool, pool.connection() as conn:
        memory = AsyncPostgresSaver(conn)
        
        return memory