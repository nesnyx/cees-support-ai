from datetime import timedelta
from app.service.chromadb import vectorstore
from utils.model import llm
from langchain_core.output_parsers import  JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_postgres import PostgresChatMessageHistory
from config.mysql import PG_DATABASE_URL
from langchain_community.chat_message_histories.redis import RedisChatMessageHistory
import uuid, psycopg

from langgraph.prebuilt import create_react_agent

with open("./prompts/fix_template.txt", "r") as file:
    FIXED_RAG_STRUCTURE = file.read()


def get_session_history(session_id: str):
    sync_connection = psycopg.connect(PG_DATABASE_URL)
    table_name = "chat_history"
    chat_history = PostgresChatMessageHistory(
        table_name, session_id, sync_connection=sync_connection
    )

    return chat_history


def retrieve_relevant_documents(question: str, user_id: str, k: int = 1):
    results = vectorstore.similarity_search_with_relevance_scores(
        question, k=k, filter={"user_id": user_id}
    )

    if not results:
        return []

    results = sorted(results, key=lambda x: x[1], reverse=True)
    return results


def perform_rag_query(user, prompt, telp_customer, question: str):
    session_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user['id']}_{telp_customer}_chat")
    )
    retriever_results = retrieve_relevant_documents(question, user["id"], k=3)

    retrieved_info = "\n\n".join([doc.page_content for doc, _ in retriever_results])
    user_persona = prompt

    system_prompt = ChatPromptTemplate.from_template(FIXED_RAG_STRUCTURE)
    final_system_prompt = system_prompt.format_messages(
        user_persona=user_persona,
        context=retrieved_info,
    )[0]
    
    template_prompt = ChatPromptTemplate.from_messages(
        [
            final_system_prompt,
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    

    rag_chain = template_prompt | llm | JsonOutputParser()
    
    chain_with_history = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    final_response = chain_with_history.invoke(
        {"input": question}, config={"configurable": {"session_id": session_id}}
    )

    return {"result": final_response}
