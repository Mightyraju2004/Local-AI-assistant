
from datetime import datetime
from utilities.utilities import log
import requests
from rag import search
import sqlite3
import json


def get_user_city():
    return "Bangalore"


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_city_weather(city):
    url = f"https://wttr.in/{city}?format=3"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text

#search_knowledge base is the tool which is used for RAG (Retrieval-Augmented Generation) to search the knowledge base for relevant information based on the user's query. It uses the search function from rag.py to find the top_k relevant chunks of text from the knowledge base and returns them as a formatted string.
def search_knowledge_base(query): #ye tool user query ko input ke roop mein leta hai aur knowledge base mein search karta hai aur top_k results return karta hai.
    results = search(query, top_k=2)

    log(f"📚 Knowledge base search: {query}")

    for r in results:
        log(f"   {r['score']:.2f} - {r['source']} #{r['chunk_id']}")

    blocks = []

    for r in results:
        sourceFileName = r["source"]
        chunkId = r["chunk_id"]
        chunkText = r["text"]

        header = f"[{sourceFileName} #{chunkId}]"
        block = f"{header}\n{chunkText}"
        blocks.append(block)

    return "\n\n".join(blocks)


# Create database and tasks table
def init_db():
    conn = sqlite3.connect("tasks.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    conn.close()


init_db()


# Tool 1: Add a task
def add_task(title):
    if not isinstance(title, str):
        return "Error: Task title must be text."

    title = title.strip()

    if not title:
        return "Error: Task title cannot be empty."

    if len(title) > 200:
        return "Error: Task title must be 200 characters or fewer."

    conn = sqlite3.connect("tasks.db")

    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            (title,)
        )

        task_id = cursor.lastrowid
        conn.commit()

        return f"Task added successfully. ID: {task_id}"

    except sqlite3.Error:
        conn.rollback()
        return "Error: Could not save the task."

    finally:
        conn.close()


# Tool 2: View all tasks
def list_tasks():
    conn = sqlite3.connect("tasks.db")

    rows = conn.execute(
        "SELECT id, title, status FROM tasks"
    ).fetchall()

    conn.close()

    if not rows:
        return "No tasks found."

    return json.dumps([
        {
            "id": row[0],
            "title": row[1],
            "status": row[2]
        }
        for row in rows
    ])


# Tool 3: Complete a task
def complete_task(task_id):
    if isinstance(task_id, bool) or not isinstance(task_id, int):
        return "Error: Task ID must be an integer."

    if task_id <= 0:
        return "Error: Task ID must be positive."

    conn = sqlite3.connect("tasks.db")

    try:
        cursor = conn.execute(
            """UPDATE tasks
               SET status = 'completed'
               WHERE id = ? AND status = 'pending'""",
            (task_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return "Error: Task not found or already completed."

        return f"Task {task_id} completed successfully."

    except sqlite3.Error:
        conn.rollback()
        return "Error: Could not update the task."

    finally:
        conn.close()


# Tool definitions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in YYYY-MM-DD HH:MM:SS format.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_weather",
            "description": "Get the weather information for a specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city for which to get weather information."
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_city",
            "description": "Returns the city where the user lives. Use this when the user says 'my city', 'where I live', or 'my location' without naming the city.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new task to the user's task list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Description of the task"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Show all saved tasks.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed using its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task to complete"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Searches the Zorvex Technologies company knowledge base: "
                "leave, medical, HR, hiring, tech, incident reports and travel "
                "expense policies. Use it for any question about company policies "
                "or documents. Returns the most relevant passages with their source."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question, rewritten as a short, self-contained search query."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# Function name to Python function mapping
FUNCTION_NAME_TO_FUNCTION_MAP = {
    "get_current_time": get_current_time,
    "get_city_weather": get_city_weather,
    "get_user_city": get_user_city,
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "search_knowledge_base": search_knowledge_base
}


# Execute the selected tool
def run_tool(tool_call):
    func_name = tool_call.function.name
    func_args = {}

    try:
        func_args = json.loads(
            tool_call.function.arguments or "{}"
        )

        log(f"🔧 {func_name}({func_args})")

        fn = FUNCTION_NAME_TO_FUNCTION_MAP[func_name]
        result = fn(**func_args)

    except Exception as e:
        result = f"Error while running {func_name}: {e}"

    log(f"   ↳ {result}")

    return str(result)
