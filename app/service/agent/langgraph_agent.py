import uuid, logging, psycopg_pool,os
from app.service.agent.tools.products import create_tools
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from utils.model import llm

load_dotenv()

logger = logging.getLogger(__name__)


class FixedLangGraphAgent:
    """Fixed LangGraph Agent dengan proper connection management"""

    def __init__(self):
        self.conninfo = os.getenv("POSTGRESQL_CONNECTION_URL")
        self.pool = None
        self.postgres_checkpointer = None
        self.initialized = False

    def create_session_id(self, user_id: str, telp_customer: str) -> str:
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"fixed_{user_id}_{telp_customer}",
            )
        )

    def create_thread_id(self, user_id: str, customer_phone: str) -> str:
        """
        Create deterministic thread ID untuk consistency
        Format: {app_prefix}_{user_id}_{customer_identifier}_{type}
        """
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"cees_ai_{user_id}_{customer_phone}",
            )
        )

    # 🔥 Production Best Practice
    def create_checkpoint_namespace(self, user_id: str, customer_phone: str) -> str:
        """
        Create checkpoint namespace untuk logical separation
        Format: {app}_{business_unit}_{user_id}
        """
        return f"cees_ai_{user_id}_{customer_phone}"

    async def initialize_persistent_resources(self):
        """Initialize persistent connection pool dan memory"""
        if self.initialized:
            return True

        try:
            # Create persistent connection pool
            self.pool = psycopg_pool.AsyncConnectionPool(
                conninfo=self.conninfo,
                max_size=10,
                min_size=5,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": 0,
                    "row_factory": dict_row,
                },
                open=False,
            )

            # Open pool
            await self.pool.open()
            logger.info("Connection pool opened successfully")

            # Get persistent connection untuk checkpointer
            self.memory_conn = await self.pool.getconn()
            # Create PostgreSQL checkpointer
            self.postgres_checkpointer = AsyncPostgresSaver(self.memory_conn)

            # Setup tables jika belum ada
            try:
                await self.postgres_checkpointer.setup()
                logger.info("PostgreSQL memory tables setup completed")
            except Exception as e:
                logger.warning(f"Memory setup warning (mungkin tables sudah ada): {e}")

            self.initialized = True
            logger.info("Persistent LangGraph agent resources initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize persistent resources: {e}")
            return False

    async def create_agent(self, user_id: str, user_persona: str):
        """Create agent dengan tools dan memory"""

        # Ensure resources are initialized
        if not self.initialized:
            success = await self.initialize_persistent_resources()
            if not success:
                raise Exception("Failed to initialize persistent resources")

        # Create tools
        tools = create_tools(user_id)

        # Create agent dengan persistent memory
        agent = create_react_agent(
            model=llm, tools=tools, checkpointer=self.postgres_checkpointer
        )
        print(f"Agent : {agent}")

        self.user_persona = user_persona
        logger.info(f"Agent created for user {user_id}")

        return agent

    async def process_query(
        self, user: str, prompt: str, telp_customer: str, question: str
    ):
        """Process query dengan fixed connection management"""

        user_id = str(user["id"])
        session_id = self.create_session_id(user_id, telp_customer)
        thread_id = self.create_thread_id(user_id, telp_customer)
        checkpoint_ns = self.create_checkpoint_namespace(
            user_id=user_id, customer_phone=telp_customer
        )
        try:
            # Create agent if not exists

            agent = await self.create_agent(user_id, prompt)

            # Config untuk memory
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                }
            }

            # System message
            system_msg = SystemMessage(
                content=f"""
                {prompt}
                Kamu adalah asisten AI Customer Service dengan akses ke alat berikut:
                - Gunakan tool sesuai kebutuhan saja (jangan panjang-panjang).
                - Jawaban pelanggan HARUS simple, Tidak usah banyak basa-basi! Fokus pada inti informasi.
                - Untuk masalah teknis, cukup katakan: "Maaf, sedang ada gangguan teknis, silakan coba lagi."
                - Jangan berikan teks pembuka atau penutup berlebih, tidak usah ada salam kecuali diminta.
                - Jawab hanya sesuai konteks pertanyaan pelanggan tapi tetap santai dan ramah dan tetap friendly.
                - Gunakan Bahasa Indonesia singkat, jelas, dan langsung ke poin.
                INSTRUKSI KHUSUS:
                - Selalu ringkas! dan Jawaban yang efisien dan efektif
                - Kalau bisa ada emoticon agar tidak begitu kaku.
                - JANGAN MENGGUNAKAN BAHASA LAIN SELAIN INDONESIA saja.
                """
            )

            user_msg = HumanMessage(content=question)

            logger.info(f"Processing query for user {user_id}")

            # Process dengan agent
            response = await agent.ainvoke(
                {"messages": [system_msg, user_msg]}, config=config
            )
            # Extract response
            if response and "messages" in response:
                final_message = response["messages"][-1]
                final_response = (
                    final_message.content
                    if hasattr(final_message, "content")
                    else str(final_message)
                )
            else:
                final_response = "No response from agent."

            return {
                "response": final_response,
                "intent": {"agent_type": "CEES-AI-AGENT-BETA"},
                "session_id": session_id,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Fixed agent query failed: {e}")
            return {
                "response": f"Error processing query: {str(e)}",
                "intent": {"error": str(e)},
                "session_id": session_id,
                "status": "error",
            }


# Global instance
ai_agent = FixedLangGraphAgent()
