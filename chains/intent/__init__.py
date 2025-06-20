from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser


with open("./prompts/intent_template.txt",'r') as file:
    intent_detection_template_str = file.read()

intent_prompt = ChatPromptTemplate.from_messages([
    ("system", intent_detection_template_str), # Gunakan template intent yang baru
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])
