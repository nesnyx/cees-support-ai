import uuid, logging, psycopg_pool
from app.service.agent.tools.products import create_tools
from typing import Dict, Any
from datetime import datetime

from langchain.agents import initialize_agent, AgentType
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row


from utils.model import llm


logger = logging.getLogger(__name__)


class FixedLangGraphAgent:
    """Fixed LangGraph Agent dengan proper connection management"""

    def __init__(self):
        self.conninfo = "postgres://user_production:kodecesar1234@arisbara.cloud:3499/cees_db?sslmode=prefer&options=-csearch_path%3Dhistory"
        self.pool = None
        self.agent = None
        self.postgres_checkpointer = None
        self.initialized = False

    def create_session_id(self, user_id: str, telp_customer: str) -> str:
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"fixed_{user_id}_{telp_customer}",
            )
        )

    def create_thread_id(
        self, user_id: str, customer_phone: str, conversation_type: str = "support"
    ) -> str:
        """
        Create deterministic thread ID untuk consistency
        Format: {app_prefix}_{user_id}_{customer_identifier}_{type}
        """
        return str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"cees_ai_{user_id}_{customer_phone}_{conversation_type}_{datetime.now().strftime('%Y%m%d')}",
            )
        )

    # 🔥 Production Best Practice
    def create_checkpoint_namespace(
        self, user_id: str, business_context: str = "cs"
    ) -> str:
        """
        Create checkpoint namespace untuk logical separation
        Format: {app}_{business_unit}_{user_id}
        """
        return f"cees_ai_{business_context}_{user_id}"

    async def initialize_persistent_resources(self):
        """Initialize persistent connection pool dan memory"""
        if self.initialized:
            return True

        try:
            # Create persistent connection pool
            self.pool = psycopg_pool.AsyncConnectionPool(
                conninfo=self.conninfo,
                max_size=10,
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
        self.agent = create_react_agent(
            model=llm, tools=tools, checkpointer=self.postgres_checkpointer
        )
        print(f"Agent : {self.agent}")
        # initial_agent = initialize_agent(
        #     tools=tools, llm=llm, agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION
        # )

        self.user_persona = user_persona
        logger.info(f"Agent created for user {user_id}")

        return True

    async def process_query(
        self, user: Dict[str, Any], prompt: str, telp_customer: str, question: str
    ) -> Dict[str, Any]:
        """Process query dengan fixed connection management"""

        user_id = str(user["id"])
        session_id = self.create_session_id(user_id, telp_customer)
        thread_id = self.create_thread_id(user_id, telp_customer)
        checkpoint_ns = self.create_checkpoint_namespace(user_id, telp_customer)
        try:
            # Create agent if not exists
            if not self.agent:
                await self.create_agent(user_id, prompt)

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

                1. **search_user_knowledge**: Untuk mencari informasi dalam basis pengetahuan (produk, layanan, FAQ)

                2. **save_order**: Untuk menyimpan pesanan ke database setelah detail lengkap & konfirmasi
                3. **check_order_status**: Untuk mengecek status pesanan berdasarkan Order ID

                INSTRUKSI PENTING:
                - Gunakan search_user_knowledge untuk menjawab pertanyaan produk/layanan
                - Gunakan check_order_status ketika pelanggan memberikan nomor pesanan

                - Gunakan save_order hanya setelah SEMUA detail dikonfirmasi pelanggan
                - Ingat percakapan sebelumnya (memory otomatis tersimpan)
                - Berikan jawaban yang ramah, akurat, dan membantu
                - Gunakan Bahasa Indonesia yang baik dan benar
                JIKA CUSTOMER MAU PESAN SERTAKAN MENU DULU JIKA BELUM ADA MENYEBUTKAN MENU
                🚨 **PERINGATAN KERAS:**
                JANGAN PERNAH menulis dalam bahasa selain Bahasa Indonesia!
                Ini adalah sistem Customer Service Indonesia!
                """
                
            )

            user_msg = HumanMessage(content=question)

            logger.info(f"Processing query for user {user_id}")

            # Process dengan agent
            response = await self.agent.ainvoke(
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

    async def get_conversation_history(self, session_id: str):
        """Method untuk mendapatkan history percakapan dari PostgreSQL"""
        try:
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": "customer_service",
                }
            }

            # Get checkpoint dari PostgreSQL
            checkpoint = await self.postgres_checkpointer.aget(config)

            if checkpoint and checkpoint.get("channel_values"):
                messages = checkpoint["channel_values"].get("messages", [])
                history = []
                for msg in messages:
                    history.append(
                        {
                            "type": "human" if isinstance(msg, HumanMessage) else "ai",
                            "content": (
                                msg.content if hasattr(msg, "content") else str(msg)
                            ),
                        }
                    )
                return history

            return []

        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def close(self):
        """Close resources"""
        try:
            if self.memory_conn:
                await self.pool.putconn(self.memory_conn)
            if self.pool:
                await self.pool.close()
            logger.info("Fixed agent resources closed")
        except Exception as e:
            logger.error(f"Error closing resources: {e}")


# Global instance
ai_agent = FixedLangGraphAgent()
