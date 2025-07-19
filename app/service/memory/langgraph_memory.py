from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import asyncio
from typing import Optional
import logging
import psycopg

logger = logging.getLogger(__name__)

class LangGraphMemoryManager:
    """Fixed memory manager dengan proper database setup"""

    def __init__(self, db_conn: str):
        self.db_conn = db_conn
        self._pool: Optional[AsyncConnectionPool] = None
        self._is_initialized = False

    async def _setup_database_schema(self):
        """Setup database schema dan tables untuk LangGraph"""
        try:
            # Use sync connection for initial setup
            conn = psycopg.connect(self.db_conn)
            conn.autocommit = True

            with conn.cursor() as cursor:
                # Create schema if not exists
                cursor.execute("CREATE SCHEMA IF NOT EXISTS public")

                # Create checkpoints table manually (karena auto-setup gagal)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history.checkpoints (
                        thread_id TEXT NOT NULL,
                        checkpoint_ns TEXT NOT NULL DEFAULT '',
                        checkpoint_id TEXT NOT NULL,
                        parent_checkpoint_id TEXT,
                        type TEXT,
                        checkpoint JSONB NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                    )
                """)

                # Create writes table for LangGraph
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history.checkpoint_writes (
                        thread_id TEXT NOT NULL,
                        checkpoint_ns TEXT NOT NULL DEFAULT '',
                        checkpoint_id TEXT NOT NULL,
                        task_id TEXT NOT NULL,
                        idx INTEGER NOT NULL,
                        channel TEXT NOT NULL,
                        type TEXT,
                        value JSONB,
                        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                    )
                """)

                # Create indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_ns 
                    ON checkpoints (thread_id, checkpoint_ns)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_created 
                    ON checkpoints (created_at)
                """)

            conn.close()
            logger.info("Database schema setup completed successfully")

        except Exception as e:
            logger.error(f"Failed to setup database schema: {e}")
            raise

    async def initialize(self):
        """Initialize connection pool dengan proper database setup"""
        if self._is_initialized:
            return

        try:
            # Setup database schema first
            await self._setup_database_schema()

            # Create pool
            self._pool = AsyncConnectionPool(
                conninfo=self.db_conn,
                max_size=20,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": 0,
                    "row_factory": dict_row,
                },
                open=False
            )

            # Open pool
            await self._pool.open()
            self._is_initialized = True

            logger.info("LangGraph memory manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {e}")
            raise

    async def get_memory_saver(self):
        """Get memory saver tanpa auto-setup (karena sudah manual setup)"""
        if not self._is_initialized:
            await self.initialize()

        if not self._pool:
            raise RuntimeError("Connection pool not initialized")

        try:
            # Get connection
            conn = await self._pool.getconn()
            memory_saver = AsyncPostgresSaver(conn)

            # SKIP setup karena sudah manual setup
            logger.info("Memory saver created successfully")

            return memory_saver

        except Exception as e:
            logger.error(f"Failed to get memory saver: {e}")
            raise

    async def close(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
            self._is_initialized = False
            logger.info("Memory manager closed")

# Global instance dengan updated connection string
memory_manager = LangGraphMemoryManager(
    db_conn="postgresql://user_production:kodecesar1234@arisbara.cloud:3499/cees_db"
)
