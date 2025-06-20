from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser


with open("./prompts/rag_template.txt",'r') as file:
    rag_template_str = file.read()

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", rag_template_str), # Gunakan template intent yang baru
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])
