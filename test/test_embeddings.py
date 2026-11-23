from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv() #by default looks for .env file

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

#now interact with ollama embedding model
response = client.embeddings.create(
    model=os.getenv("EMBEDDING_MODEL"),
    input=["Hello, my dog is cute", "Hello, my cat is cute"] #is input ka embedding generate karega ollama embedding model as a response
)

# print(len(response.data[0].embedding)) #data is array(response ka data).response.data[0] represents pehla string of input array
# print(response.data[1].embedding)
 
for i , emb in enumerate(response.data):
    print(f"Embedding {i} length: {len(emb.embedding)}")

