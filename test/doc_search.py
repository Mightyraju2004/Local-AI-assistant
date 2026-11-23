#The Ollama server must be running to serve models downloaded through Ollama to your applications.
import os
import numpy
from openai import OpenAI 
# openai package se OpenAI class import kar rahe hain.
# client = OpenAI() =>Yahan client ke through hum openAI API ko requests bhej sakte hain.
from dotenv import load_dotenv
# Iska use .env file ke andar stored environment variables ko Python ke environment mein load karne ke liye hota hai.


load_dotenv() #by default looks for .env file
#Iska kaam .env file ke andar stored variables ko Python ke environment mein load karna hai.

 #initialization of openAI client with base_url and api_key
#  client ek variable hai jisme OpenAI() ka object store hota hai.
# Jab hum OpenAI() likhte hain, toh iska ek object create hota hai.
client = OpenAI(
    base_url=os.getenv("BASE_URL"), #BASE_URL environment variable se base URL ko fetch
    api_key=os.getenv("API_KEY") #API_KEY environment variable se API key ko fetch
)

EMBED_MODEL=os.getenv("EMBED_MODEL")
KB_FOLDER=os.getenv("KB_FOLDER")


#get the embedding of a text from the embedding model
def get_embedding(text):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text #input mein  vo text pass kar rahe hain jis text ka embedding generate karna hai.
    )
    return response.data[0].embedding 

#Get the cosine similarity between two embeddings or vectors
def cosine_similarity(A, B):
    dot_prod = numpy.dot(A, B) #numpy.dot() ka use karke A aur B ke beech ka dot product calculate kar rahe hain.
    norm_a = numpy.linalg.norm(A) #numpy.linalg.norm() ka use karke A ka norm calculate kar rahe hain.
    norm_b = numpy.linalg.norm(B) #numpy.linalg.norm() ka use karke B ka norm calculate kar rahe hain.
    return dot_prod / (norm_a * norm_b) #cosine similarity ka formula: dot product divided by the product of the norms of the two vectors.



#Load the documents from the knowledge base folder
def load_documents(folder=KB_FOLDER):#default folder is KB_FOLDER, agar user koi folder specify nahi karta hai toh ye default folder use karega.
    documents = []
    for filename in sorted(os.listdir(folder)): #sorted() function ka use karke folder ke andar ke files ko alphabetical order mein sort kar rahe hain.
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(folder, filename) #os.path.join() ka use karke folder aur filename ko join karke complete path create kar rahe hain.
        with open(path, "r", encoding="utf-8") as f:# open() function ka use karke file ko read mode mein open kar rahe hain aur encoding ko "utf-8" set kar rahe hain.
                documents.append(
                    {
                        "source": filename,
                        "text": f.read(),
                    }
                )

    return documents #documents list ko return kar rahe hain jisme har ek document ke liye ek dictionary store hai jisme "source" aur "text" keys hain.


#Add embeddings to the documents
def add_embeddings(documents):
    for document in documents:
        vector = get_embedding(document["text"]) #get_embedding() function ka use karke document ke text ka embedding generate kar rahe hain.
        document["vector"] = vector #document dictionary mein "vector" key ke andar embedding store kar rahe hain.(if vector key not present then create a new key "vector" and store the embedding in it.)

    return documents 


#search method to search the top_k documents for a user_query using cosine similarity
def search_documents(query, documents, top_k=3): #query is user query here,default top_k is 3, agar user koi value specify nahi karta hai toh ye default value use karega.
    query_vector=get_embedding(query) #get_embedding() function ka use karke user_query ka embedding generate kar rahe hain.

    results = [] #results list create kar rahe hain jisme top_k documents store honge.(list stores key-value pairs of document source, text and score)
    for document in documents:
        score = cosine_similarity(query_vector, document["vector"]) #cosine_similarity() function ka use karke user_query aur document ke embedding ke beech ka similarity score calculate kar rahe hain.
        results.append(
            {
                "score": float(score), #score ko float mein convert karke results list mein append kar rahe hain.
                "source": document["source"],
                "text": document["text"],
                "size": len(document["text"])
            }
        )

    results.sort(key=lambda rec: rec["score"], reverse=True) #results list ko score ke basis pe descending order(reverse=True) mein sort kar rahe hain.
    #har ek record mai ek rec["score"] naam ka field hai jisme score store hai, aur hum uske basis pe sort kar rahe hain.
    return results[:top_k] #top_k documents ko return kar rahe hain.(0 se top_k-1 tak ke documents ko return kar rahe hain.)

#test function to test the search_documents function
def test(user_query,documents,top_k=3):
       print(f"\n User Query: {user_query}\n")
       results = search_documents(user_query, documents, top_k)
       for result in results:
             print(f" {result['score']:.2f} - {result['source']} - {result['size']} characters)")


#Let's start testing
documents = load_documents() # documents variable mein load_documents() function ka output store kar rahe hain, jisme knowledge base folder ke andar ke documents load honge.
documents = add_embeddings(documents)

print(f"We have embedded {len(documents)} documents")

user_query = "How many days I will get for maternity leave ?"
test(user_query, documents, 3)

# 1. What are Tokens?
# Definition: Tokens are the smallest units of text that an LLM processes to understand input and generate output. A token can be a word, part of a word, or a character.

# For example:

# I love Python

# This text may be divided into tokens like:
# - I
# - love
# - Python
# Simple meaning: Tokens are the units used to measure how much text an LLM processes.
# 2. What is a Context Window?
# Definition: A context window is the maximum number of tokens an LLM can process in a single request, including the provided conversation history, current input, and space for the generated response.

# Simple meaning: It is the memory space available to an LLM for understanding the current conversation and generating a response.