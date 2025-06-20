from pydantic import BaseModel

class PromptInput(BaseModel):
    system_template : str