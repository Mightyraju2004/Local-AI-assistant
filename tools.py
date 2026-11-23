from datetime import datetime
from utilities.utilities import log
import requests
import sqlite3
import json

def get_user_city():
    return "Bangalore"  # Replace with your desired city

def get_current_time(): #method or tool or function to get current time
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_city_weather(city): #method or tool or function to get weather of city
    url = f"https://wttr.in/{city}?format=3" #url to get weather of city
    response=requests.get(url,timeout=10) #requests.get() is used to send a GET request to the specified URL and retrieve the response from the server.timeout=10 means that if the server does not respond within 10 seconds, the request will be aborted and an exception will be raised.
    response.raise_for_status() #raise_for_status() is used to raise an exception if the HTTP request returned an unsuccessful status code. If the response was successful (status code 200), this method does nothing. If the response was unsuccessful (e.g., 404, 500), it raises an HTTPError exception with information about the error.
    return response.text #response.text is used to get the content of the response as a string. It returns the text of the response, which can be useful for extracting information or displaying it to the user.



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

#TOOLS =[{tool1},{tool2},{tool3}] #tools is array or list

TOOLS = [ #information of tools used

    {
      "type" : "function", #type of tool is function
      "function" : {
             "name" : "get_current_time", 
             "description" : "Get the current date and time in YYYY-MM-DD HH:MM:SS format.",#tool ka description aesa do ki model ko aasani se samajh aa jaye ki ye tool kya karta hai
             "parameters" : { "type" : "object", "properties" : {}}
      }
    },
    {
      "type" : "function",
      "function" : {
             "name" : "get_city_weather",
             "description" : "Get the weather information for a specified city.",
             "parameters" : { "type" : "object", "properties" : { "city" : { "type" : "string", "description" : "The name of the city for which to get weather information." }},"required" : ["city"]}
      }
    },
    {
        "type" : "function",
        "function" : {
                 "name" : "get_user_city",
                 "description" : "Returns the city where the user lives.use this when the user says 'my city' or 'where I live'or 'my location' without naming the city.",
                 "parameters" : { "type" : "object", "properties" : {}}
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
    }
]

FUNCTION_NAME_TO_FUNCTION_MAP = { #key-value pair
    "get_current_time" : get_current_time,
    "get_city_weather" : get_city_weather,
    "get_user_city" : get_user_city,
    "add_task" : add_task,
    "list_tasks" : list_tasks,
    "complete_task" : complete_task
}

def run_tool(tool_call):
    func_name = tool_call.function.name
    func_args = {}

    try:
        func_args = json.loads(tool_call.function.arguments or "{}")
        log(f"🔧 {func_name}({func_args})")
        fn = FUNCTION_NAME_TO_FUNCTION_MAP[func_name]
        result = fn(**func_args)
    except Exception as e:
        result = f"Error while running {func_name} : {e}"

    log(f"   ↳ {result}")
    return str(result)

#    func_name = tool_call.function.name
#       # 2. Fixed typo: arguements -> arguments
#       func_args={}

#       try:
#            func_args = json.loads(tool_call.function.arguments or "{}") #json.loads() is used to parse a JSON string and convert it into a Python dictionary.dictionary is a data structure that stores key-value pairs, allowing you to access values using their corresponding keys.
#            fn = FUNCTION_NAME_TO_FUNCTION_MAP[func_name]
#            result = fn(**func_args) #calling of function with unpacked arguements#deferencing operator is used to unpack the dictionary and pass its key-value pairs as keyword arguments to the function.arguements are parameters or inputs that are passed to a function when it is called. 
#       except Exception as e:
#            result = f"Error while running '{func_name}': {e}"