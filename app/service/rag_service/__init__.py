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
import os

with open("./prompts/fix_template.txt",'r') as file:
    FIXED_RAG_STRUCTURE = file.read()

if not os.path.exists("history"):
    os.makedirs("history")


def perform_rag_query(user,prompt, question: str):
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3, "filter": {"user_id": user['id']}}
    )
    
    relevant_docs = retriever.invoke(question)
    retrieved_info = "\n".join([doc.page_content for doc in relevant_docs[:5]])
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
        lambda session_id: FileChatMessageHistory(f"history/user_{session_id}_chat.json"),
        input_messages_key="input",
        history_messages_key="history",
    )

    response = chain_with_history.invoke(
        {"input": question},
        config={"configurable": {"session_id": str(user['id'])}}
    )
    
    return response