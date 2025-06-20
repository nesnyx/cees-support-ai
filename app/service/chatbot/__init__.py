# from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain.memory.chat_message_histories import FileChatMessageHistory
# from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.retrievers import EnsembleRetriever
# from utils.vectoredatabase import FaissVectorStoreLoader
# from config.db import db
# from chains import main_chain_prompt
# from chains.intent import intent_detection_template_str
# from chains.rag import rag_prompt

# with open("./prompts/rag_template.txt",'r') as file:
#     system_template = file.read()


# embedding_loader = FaissVectorStoreLoader()
# # === PERBAIKAN DIMULAI DI SINI ===

# # 1. Buat list kosong untuk menampung retriever yang aktif
# active_retrievers = []
# retriever_weights = []

# # 2. Coba buat retriever untuk 'product'
# print("--- Menginisialisasi retriever produk ---")
# product_documents = db.product.get()
# product_retriever = embedding_loader.load_or_create(product_documents, index_name="product")
# if product_retriever:
#     active_retrievers.append(product_retriever)
#     retriever_weights.append(0.5) # Bobot untuk produk

# # 3. Coba buat retriever untuk 'sablon_info'
# print("\n--- Menginisialisasi retriever info sablon ---")
# sablon_info_documents = db.sablon_info.get()
# sablon_info_retriever = embedding_loader.load_or_create(sablon_info_documents, index_name="sablon_info")
# if sablon_info_retriever:
#     active_retrievers.append(sablon_info_retriever)
#     retriever_weights.append(0.5) # Bobot untuk info sablon

# if not active_retrievers:
#     raise ValueError("Tidak ada data yang dapat diindeks. Retriever tidak dapat dibuat. Aplikasi tidak dapat dimulai.")

# print(f"\n[INFO] Membuat EnsembleRetriever dengan {len(active_retrievers)} retriever aktif.")
# ensemble_retriever = EnsembleRetriever(
#     retrievers=active_retrievers, weights=retriever_weights
# )

# class ChatBotService:
#     def __init__(self, system_template, llm, session_id, question):
#         self.system_template = system_template
#         self.llm = llm
#         self.session_id = session_id
#         self.question = question
#         self.ensemble_retriever = ensemble_retriever
        

#         # BEST PRACTICE EVER
#         self.intent_prompt = ChatPromptTemplate.from_messages([
#             ("system", intent_detection_template_str), # Gunakan template intent yang baru
#             MessagesPlaceholder(variable_name="history"),
#             ("human", "{input}")
#         ])
#         self.intent_chain = self.intent_prompt | self.llm | JsonOutputParser()

#     def get_by_session_id(self):
#         return FileChatMessageHistory(f"history/{self.session_id}.json")
    
#     def chain_with_story(self):

#         intent_detection_with_history = RunnableWithMessageHistory(
#             self.intent_chain,
#             self.get_by_session_id,
#             input_messages_key="input",
#             history_messages_key="history",
#         )
#         detected_intent_json = intent_detection_with_history.invoke(
#             {"input": self.question},
#             config={"configurable": {"session_id": self.session_id}}
#         )
#         print(f"[DEBUG] Detected Intent JSON: {detected_intent_json}")

#         relevant_docs = self.ensemble_retriever.invoke(self.question)
#         retrieved_info = "\n".join([doc.page_content for doc in relevant_docs])
        

#         current_main_system_prompt_filled = self.system_template.format(
#             business_name="BROKER PROJECT",
#             retrieved_info=retrieved_info,
#         )

#         prompt = ChatPromptTemplate.from_messages([
#             ("system",current_main_system_prompt_filled),
#             MessagesPlaceholder(variable_name="history"),
#             ("human",self.question)
#         ])
        
#         chain = prompt | self.llm | StrOutputParser()

#         chain_invoke = RunnableWithMessageHistory(
#             chain,
#             self.get_by_session_id,
#             input_messages_key="input",
#             history_messages_key="history"
#         )
#         final_response_text = chain_invoke.invoke(
#             {"input": self.question},
#             config={"configurable": {"session_id": self.session_id}}
#         )
#         return {
#             "text_response": final_response_text,
#             "intent_data": detected_intent_json
#         }