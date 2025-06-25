from sqlalchemy.orm import Session
from app.router.products.model import ProductID, ProductInput, ProductModel
from utils.chromadb import collection, embedding_model,client
from app.service.chromadb import vectorstore
from utils.model import llm
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory.chat_message_histories import FileChatMessageHistory
from langchain_postgres import PostgresChatMessageHistory
from config.mysql import PG_DATABASE_URL
import os,uuid,psycopg


THRESHOLD_TINGGI = 0.85  # Jalur A: Sangat yakin, jawab langsung.
THRESHOLD_SEDANG = 0.70  # Jalur B: Cukup mirip, minta klarifikasi.

with open("./prompts/fix_template.txt",'r') as file:
    FIXED_RAG_STRUCTURE = file.read()


with open("./prompts/intent_template_cs.txt",'r') as file:
    INTENT_STRUCTURE = file.read()

if not os.path.exists("history"):
    os.makedirs("history")


def get_session_history(session_id : str) -> PostgresChatMessageHistory:
        sync_connection = psycopg.connect(PG_DATABASE_URL)
        table_name = "chat_history"
        chat_history = PostgresChatMessageHistory(
            table_name,
            session_id,
            sync_connection=sync_connection
        )
        return chat_history


def perform_rag_query(user,prompt,telp_customer, question: str):
    session_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user['id']}_{telp_customer}_chat"))
    retriever = vectorstore.similarity_search_with_relevance_scores(
        question,
        k=3,
        filter={"user_id": user['id']}
    )
    

    intent_prompt = ChatPromptTemplate.from_messages([
        ("system", INTENT_STRUCTURE), # Gunakan template intent yang baru
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    intent_chain = intent_prompt | llm | JsonOutputParser()
    intent_detection_with_history = RunnableWithMessageHistory(
            intent_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="history",
    )

    detected_intent_json = intent_detection_with_history.invoke(
            {"input": question},
            config={"configurable": {"session_id": session_id}}
    )

    
    # relevant_docs = retriever.invoke(question)
    retrieved_info = "\n".join([doc.page_content for doc,score in retriever[:5]])
    user_persona = prompt

    final_system_prompt = FIXED_RAG_STRUCTURE.format(user_persona=user_persona, context=retrieved_info)


    template_prompt = ChatPromptTemplate.from_messages([
        ("system", final_system_prompt),
        MessagesPlaceholder(variable_name="history"), 
        ("human", "{input}")
    ])


    
    rag_chain = template_prompt | llm | StrOutputParser()
    chain_with_history = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    final_response = chain_with_history.invoke(
        {"input": question},
        config={"configurable": {"session_id": session_id}}
    )
    
    return {
        "response" : final_response,
        "intent" : detected_intent_json
    }