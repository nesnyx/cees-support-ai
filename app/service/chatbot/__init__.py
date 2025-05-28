from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory.chat_message_histories import FileChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
from utils.vectoredatabase import FaissVectorStoreLoader
from config.database import db

with open("system_template.txt",'r') as file:
    system_template = file.read()

embedding_loader = FaissVectorStoreLoader()
product_retriever = embedding_loader.load_or_create(db.product.get(), index_name="product")
sablon_info_retriever = embedding_loader.load_or_create(db.sablon_info.get(),index_name="sablon_info")

ensemble_retriever = EnsembleRetriever(
    retrievers=[product_retriever, sablon_info_retriever], weights=[0.5, 0.5]
)

class ChatBotService:
    def __init__(self, system_template, llm, session_id, question):
        self.system_template = system_template
        self.llm = llm
        self.session_id = session_id
        self.question = question
        self.ensemble_retriever = ensemble_retriever
       
    def get_by_session_id(self):
        return FileChatMessageHistory(f"history/{self.session_id}.json")
    
    def chain_with_story(self):
        relevant_docs = self.ensemble_retriever.invoke(self.question)
        retrieved_info = "\n".join([doc.page_content for doc in relevant_docs])
        
        filled_template = self.system_template.format(
            business_name="SablonGanteng",
            retrieved_info=retrieved_info,
            question=self.question
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system",filled_template),
            MessagesPlaceholder(variable_name="history"),
            ("human","{input}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()

        chain_invoke = RunnableWithMessageHistory(
            chain,
            self.get_by_session_id,
            input_messages_key="input",
            history_messages_key="history"
        )
        return chain_invoke.invoke({
            "business_name":"SablonGanteng",
            "input" : self.question,
            
        },config={"configurable":{"session_id" : self.session_id}})