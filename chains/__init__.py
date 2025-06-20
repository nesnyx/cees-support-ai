
def  main_chain_prompt(llm,prompt,output_parser):
    chain = prompt | llm | output_parser
    return chain