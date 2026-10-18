import json
import os
from dotenv import load_dotenv
from openai import OpenAI #Library OpenAI ki hai
#we have to use openai library to call llm api because it is standard protocol for developers of ai in world,we have to import openai if we want to write api using openai standard.
#openai is standard api.openai ne chatgpt bnaya
# client.chat.completions.create method hai, yeh sirf aur sirf openai package ke andar hi likha hua hai.
# OpenAI Standard Protocol ban chuka hai:
# Jab AI world me OpenAI mashhoor hua, toh openai ka code likhne ka tareeka (client.chat.completions.create) sabse zyada use hone laga aur jagah bhi.
#ollama sends response into json format but we use openai so wo json format ko object mai convert krdeta hai
# to basically humare code mai ollama ka llm model qwen3:4b use ho rha hai but written format open ai ka use ho rha hai,to use written format of openai, we have to use openai library
from tools import FUNCTION_NAME_TO_FUNCTION_MAP, TOOLS

load_dotenv()

client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY")) #if we write only OpenAI() then it will call OpenAI ak koi bhi default model and api key but hume apna model and api key use karna hai so we have to pass out base_url and api_key in OpenAI() function

MAX_HISTORY_MESSAGES = 12
MAX_TOOL_ROUNDS = 3


def trim_history():
    global messages

    history = [
        item for item in messages[1:]
        if item.get("role") in ("user", "assistant")
        and isinstance(item.get("content"), str)
        and item["content"].strip()
    ]

    messages[:] = [messages[0]] + history[-MAX_HISTORY_MESSAGES:]

messages = [
    {
        "role": "system",
        "content": (
        "You are a helpful personal productivity assistant. "
        "Reply in English and keep answers concise. "
        "Use available tools to add, list, and complete tasks. "
        "Never claim an action succeeded unless the tool result confirms it. "
        "If a tool fails, inspect the error and correct the arguments "
        "when possible. Do not repeat a failing action indefinitely. "
        "Ask the user for clarification if required information is missing. "
        "Do not claim access to live information unless a suitable tool "
        "provides it."
        ),
    }
]

print("Chatbot started! Type 'exit' to quit.\n")

while True: #loop to keep the chatbot running until the user decides to exit
  user_input = input("\nShubhanshu: ")

  if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
    print("Assistant: Goodbye!")
    break

  trim_history()  # Sliding-window memory

  messages.append({"role": "user", "content": user_input})
  print("Assistant is thinking...")

  #ist call to llm api with tools
  # 1. Added comma after messages=messages
  #ist llm api call mai hum query mai avaliable tools aur puri message list bhejenge phir llm khud context samajhke tools bhejega ki konsa tool required hai
  response = client.chat.completions.create(
      model=os.getenv("MODEL"), messages=messages, tools=TOOLS
  )

  msg = response.choices[0].message

  # if msg.tool_calls:
  #   messages.append(msg)

  #   for tool_call in msg.tool_calls:
  #     func_name = tool_call.function.name
  #     # 2. Fixed typo: arguements -> arguments
  #     func_args = json.loads(tool_call.function.arguments or "{}") #json.loads() is used to parse a JSON string and convert it into a Python dictionary.dictionary is a data structure that stores key-value pairs, allowing you to access values using their corresponding keys.

  #     fn = FUNCTION_NAME_TO_FUNCTION_MAP[func_name]
  #     result = fn(**func_args) #calling of function with unpacked arguements#deferencing operator is used to unpack the dictionary and pass its key-value pairs as keyword arguments to the function.arguements are parameters or inputs that are passed to a function when it is called. 
  #     messages.append({
  #         "role": "tool",
  #         "tool_id": tool_call.id,  #konsa tool hai vo bhi pata hona chahiye thats why we are storing tool_id
  #         "content": str(result),
  #     })
  #   #for block ends

  #   # 2nd call to llm api after tool execution to get the final response from the assistant(like its currently 8:30 pm in tokyo)
  #   response = client.chat.completions.create(
  #       model=os.getenv("MODEL"), messages=messages
  #   )

  #   msg = response.choices[0].message #abhi jo assistant ka response hai recently waala after calling llm api usko msg variable me store kar diya

  # #if condition ends
  # messages.append({"role": "assistant", "content": msg.content}) 

  # print("Assistant:" + msg.content) #recently waala message ka response print kar diya

    # 5. Extract and print the response INSIDE the loop
    # reply = response.choices[0].message.content
    # print("Assistant: " + reply)
    # print(response.choices[0].message.role); #assistant

    # # 6. Save assistant's reply to history for context
    # messages.append({"role": "assistant", "content": reply})
    
  
  if msg.tool_calls:
      messages.append(msg.model_dump(exclude_none=True))
      tool_rounds = 0

      while msg.tool_calls and tool_rounds < MAX_TOOL_ROUNDS:
          tool_rounds += 1

          for tool_call in msg.tool_calls:
              func_name = tool_call.function.name

              try:
                  func_args = json.loads(
                      tool_call.function.arguments or "{}"
                  )

                  if not isinstance(func_args, dict):
                      raise ValueError("Arguments must be a JSON object.")

                  fn = FUNCTION_NAME_TO_FUNCTION_MAP.get(func_name)

                  if fn is None:
                      raise ValueError(f"Unknown tool: {func_name}")

                  result = fn(**func_args)

              except (ValueError, TypeError) as error:
                  result = f"Tool error: {error}. Correct the arguments."

              except Exception as error:
                  print("Tool execution error:", error)
                  result = "Tool execution failed. Do not claim success."

              messages.append({
                  "role": "tool",
                  "tool_call_id": tool_call.id,
                  "content": str(result),
              })

          response = client.chat.completions.create(
              model=os.getenv("MODEL"),
              messages=messages,
              tools=TOOLS,
          )
          msg = response.choices[0].message

      if msg.tool_calls:
          final_answer = (
              "I couldn't complete the request within the allowed "
              "number of tool rounds. Please try again."
          )
      else:
          final_answer = msg.content or "I couldn't generate a response."

  else:
      final_answer = msg.content or "I couldn't generate a response."

  messages.append({"role": "assistant", "content": final_answer})
  print("Assistant:", final_answer)

