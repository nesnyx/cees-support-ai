import uuid
import logging
from typing import Dict, Any, List
from datetime import datetime
from typing_extensions import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from app.service.chromadb import vectorstore
from utils.model import llm

logger = logging.getLogger(__name__)

# Load prompts
with open("./prompts/fix_template.txt", "r") as file:
    FIXED_RAG_STRUCTURE = file.read()

# FIXED: Gunakan TypedDict untuk LangGraph state
class CustomerServiceState(TypedDict):
    """State schema untuk LangGraph workflow"""
    messages: str
    context: str
    user_id: str
    session_id: str
    response: str
    prompt: str
    intent: Dict[str, Any]

class LangGraphRAGService:
    """Fixed RAG service menggunakan LangGraph"""

    def create_session_id(self, user_id: str, telp_customer: str):
        """Generate session ID"""
        return str(uuid.uuid5(
            uuid.NAMESPACE_DNS, 
            f"cs_{user_id}_{telp_customer}_{datetime.now().strftime('%Y%m%d_%H')}"
        ))

    async def retrieve_documents(self, question: str, user_id: str, k: int = 3) -> List[tuple]:
        """Retrieve relevant documents"""
        try:
            results = vectorstore.similarity_search_with_relevance_scores(
                question, k=k, filter={"user_id": user_id}
            )
            return sorted(results, key=lambda x: x[1], reverse=True) if results else []
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []

    def create_rag_workflow(self):
        """Create simple RAG workflow dengan LangGraph"""

        async def retrieve_step(state: CustomerServiceState):
            """Step 1: Retrieve relevant documents"""
            logger.info(f"Retrieving documents for user {state['user_id']}")

            docs = await self.retrieve_documents(
                state["messages"], 
                state["user_id"], 
                k=3
            )

            if docs:
                state["context"] = "\n\n".join([doc.page_content for doc, _ in docs])
                logger.info(f"Retrieved {len(docs)} documents")
            else:
                state["context"] = "Tidak ada informasi yang relevan ditemukan."
                logger.warning("No relevant documents found")

            return state

        async def generate_response_step(state: CustomerServiceState) :
            """Step 2: Generate response using LLM"""
            logger.info("Generating response")

            try:
                system_prompt = ChatPromptTemplate.from_template(FIXED_RAG_STRUCTURE)
                final_system_prompt = system_prompt.format_messages(
                    user_persona=state["prompt"],
                    context=state["context"],
                )[0]
                
                template_prompt = ChatPromptTemplate.from_messages(
                    [
                        final_system_prompt,
                        ("human", "{input}"),
                    ]
    )
                chain = template_prompt | llm | JsonOutputParser()
                
                response = await chain.ainvoke({
                    "input": state["messages"]
                })

                state["response"] = response.get("response", str(response))
                state["intent"] = response.get("intent", {})

                logger.info("Response generated successfully")

            except Exception as e:
                logger.error(f"Response generation failed: {e}")
                state["response"] = "Maaf, terjadi kesalahan dalam memproses permintaan Anda."
                state["intent"] = {"error": str(e)}

            return state

        # Build workflow graph
        workflow = StateGraph(CustomerServiceState)
        workflow.add_node("retrieve", retrieve_step)
        workflow.add_node("generate", generate_response_step)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()

    async def process_query(
        self, 
        user, 
        prompt: str, 
        telp_customer: str, 
        question: str
    ) :
        """Main method untuk memproses query"""

        session_id = self.create_session_id(str(user['id']), telp_customer)

        # FIXED: Create state sebagai dictionary
        state: CustomerServiceState = {
            "messages":question,
            "context": "",
            "user_id": str(user['id']),
            "session_id": session_id,
            "response": "",
            "prompt": prompt,
            "intent": {}
        }

        try:
            # Create workflow tanpa complex memory untuk sekarang
            workflow = self.create_rag_workflow()

            # Run workflow tanpa checkpointing dulu
            result_state = await workflow.ainvoke(state)

            return {
                "response": result_state["response"],
                "intent": result_state["intent"],
                "session_id": session_id,
                "context_length": len(result_state["context"]),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "response": "Maaf, terjadi kesalahan dalam memproses permintaan Anda.",
                "intent": {"error": str(e)},
                "session_id": session_id,
                "status": "error"
            }

# Global service instance
langgraph_rag_service = LangGraphRAGService()
