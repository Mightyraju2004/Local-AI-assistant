import chromadb
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


# chroma = chromadb.Client() #client() creates a new client object that can be used to interact with the Chroma database.#chromadb ka client

client = OpenAI( #openai ka client(object) create karne ke liye
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

EMBED_MODEL = os.getenv("EMBED_MODEL")

#Get the embedding of a text using EMBED_MODEL
def get_embedding(text):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return response.data[0].embedding


chunks = {
    "c0": "Leave Policy - Maternity Leave\nMaternity leave is 26 weeks of paid leave for the first two children.",
    "c1": "Medical Policy - Maternity Cover\nHospitalization for childbirth is covered up to 75,000 rupees.",
    "c2": "Travel Expense - Reimbursement\nSubmit expense claims within 30 days of the trip. Approved claims are reimbursed within 7 working days.",
    "c3": "Tech Docs - Deployment Windows\nProduction deployments are allowed on Tuesdays and Thursdays between 11 AM and 4 PM.",
}

ids = list(chunks.keys()) #this creates a list of keys from the chunks dictionary, which will be used as unique identifiers for each document in the collection.
documents = list(chunks.values())# this creates a list of values from the chunks dictionary, which will be used as the actual content of each document in the collection.

embeddings = []
for s in documents:
    embedding = get_embedding(s)
    embeddings.append(embedding)


chroma = chromadb.PersistentClient(path="./chromadbStorage") # PersistentClient() creates a new persistent client object that can be used to interact with the Chroma database. The path parameter specifies the location where the database will be stored on disk.


#In ChromaDB, a Collection is used to store and manage related documents, their embeddings, and metadata together.
zorvex_collection = chroma.get_or_create_collection(
    name="zorvex_technology",
    configuration={
        "hnsw": { #HNSW (Hierarchical Navigable Small World) ek algorithm hai jo vector database mein approximate nearest neighbor search efficiently perform karta hai.It is fast search algo.
# Simple words mein: Jab user query karta hai, toh HNSW relevant vectors ko efficiently find karne mein help karta hai.
            "space": "cosine", #cosine distance is used to measure the similarity between two vectors. It is defined as 1 minus the cosine of the angle between the vectors. The smaller the cosine distance, the more similar the vectors are.
            #Ye specify karta hai ki vectors ke beech distance calculate karne ke liye cosine distance use karni hai.
#             Example:
# - Cosine similarity = 1 → Distance = 0 (identical direction)
# - Cosine similarity = 0 → Distance = 1
        }
    }
)

zorvex_collection.upsert( #It will update if an Id is existing, otherwise it will insert a new record
    ids=ids,
    documents=documents,
    embeddings=embeddings,
)


query = "When is the production deployment allowed ? "
query_embdding = get_embedding(query) #user query ka embedding generate karne ke liye get_embedding() function call kiya ja raha hai, jo OpenAI API ka use karke query text ko vector representation mein convert karta hai.

results = zorvex_collection.query(
    query_embeddings=[query_embdding], #user query ka embedding pass kiya ja raha hai, jisse ChromaDB mein stored document embeddings ke saath similarity search perform kiya ja sake.
    n_results=2 # Ye specify karta hai ki query ke liye kitne relevant results retrieve karne hain. Yahan n_results=1 ka matlab hai ki sirf top 1 relevant document retrieve karna.
    #top k results ko n_results bol rhe hain.
)
#.query() method retrieves the most relevant chunks from documents with user query by performing similarity search between the user's query embedding and the stored document embeddings."
#here we use cosine distance so Most relevant chunks = Jinka cosine distance sabse kam hota hai user query se.(cosine similarity jyada hota hai between user query and document embedding)ss


print(results["documents"][0]) #documents mai bahut saare results aa jate hain, hum sirf top 1 result print kar rahe hain jo ki best similarity score ke saath match karta hai user query ke saath(simillarity score humne cosine distance(between user query and document chunks embedding) ke basis pe calculate kiya hai).
