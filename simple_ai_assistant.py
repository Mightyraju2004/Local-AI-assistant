# import json
# #standard library imports
# import os

# #third-party imports
# from dotenv import load_dotenv
# from openai import OpenAI #Library OpenAI ki hai
# #we have to use openai library to call llm api because it is standard protocol for developers of ai in world,we have to import openai if we want to write api using openai standard.
# #openai is standard api.openai ne chatgpt bnaya
# # client.chat.completions.create method hai, yeh sirf aur sirf openai package ke andar hi likha hua hai.
# # OpenAI Standard Protocol ban chuka hai:
# # Jab AI world me OpenAI mashhoor hua, toh openai ka code likhne ka tareeka (client.chat.completions.create) sabse zyada use hone laga aur jagah bhi.
# #ollama sends response into json format but we use openai so wo json format ko object mai convert krdeta hai
# # to basically humare code mai ollama ka llm model qwen3:4b use ho rha hai but written format open ai ka use ho rha hai,to use written format of openai, we have to use openai library

# #local modules
# from tools import TOOLS, run_tool #run_tool is method to run the tool and get the result of the tool call
# from utilities.utilities import log #log is method to print debug messages in gray color, it is used to print debug messages in gray color when DEBUG environment variable is set to True.

# load_dotenv()

# client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY")) #if we write only OpenAI() then it will call OpenAI ak koi bhi default model and api key but hume apna model and api key use karna hai so we have to pass out base_url and api_key in OpenAI() function

# MAX_STEPS = 5  # Maximum number of tool calls to prevent infinite tool calling ot infinite loops

# messages = [
#     {
#         "role": "system",
#         "content": (
#     "You are a helpful general-purpose AI assistant and personal productivity assistant. "
#     "Reply in concise English. "
#     "Answer general knowledge questions using your existing knowledge. "
#     "Do not use tools for simple factual questions unless necessary. "
#     "Use available tools for task management, current time, and weather when appropriate. "
#     "Never claim a tool succeeded unless its result confirms it."
# )
        
#     }
# ]

# print("Chatbot started! Type 'exit' to quit.\n")

# while True: #loop to keep the chatbot running until the user decides to exit
#   user_input = input("\nShubhanshu: ")

#   if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
#     print("Assistant: Goodbye!")
#     break


#   messages.append({"role": "user", "content": user_input})
#   print("Assistant is thinking...")

#   #ist call to llm api with tools
#   # 1. Added comma after messages=messages
#   #ist llm api call mai hum query mai avaliable tools aur puri message list bhejenge phir llm khud context samajhke tools bhejega ki konsa tool required hai


# # chained tool calling
#   for step in range(MAX_STEPS): #loop to limit the number of tool calls to prevent infinite loops

#     #call to llm api(request to llm api by user query) with tools.by this call we get response from llm api
#     response = client.chat.completions.create(
#           model=os.getenv("MODEL"), messages=messages, tools=TOOLS
#       )
    
#     msg = response.choices[0].message

#     if not msg.tool_calls:  #if tool_calls is empty then break the loop
#       break

#     log(f"Step {step + 1}: model requested {len(msg.tool_calls)}tool call(s).")

#     messages.append(msg)

#     for tool_call in msg.tool_calls:
#       result = run_tool(tool_call) #run_tool is method to run the tool and get the result of the tool call
      
#       messages.append({
#           "role": "tool",
#           "tool_call_id": tool_call.id,  #konsa tool hai vo bhi pata hona chahiye thats why we are storing tool_id
#           "content": str(result),
#       })
#     #for block ends

#   else:
#        #ran out of steps,model will never gave the final answer
#        fallback="Sorry, I couldn't complete the task within the step limit. Please try again."
#        messages.append({"role": "assistant", "content": fallback})
#        print("Assistant:" + fallback)
#        continue

#     # # 2nd call to llm api after tool execution to get the final response from the assistant(like its currently 8:30 pm in tokyo)
#     # response = client.chat.completions.create(
#     #     model=os.getenv("MODEL"), messages=messages
#     # )

#     # msg = response.choices[0].message #abhi jo assistant ka response hai recently waala after calling llm api usko msg variable me store kar diya

#   #if condition ends
#   messages.append({"role": "assistant", "content": msg.content}) 

#   print("Assistant:" + msg.content or "") #recently waala message ka response print kar diya

   
    
  
# standard library imports
import os

# Third-party imports
from openai import OpenAI
from dotenv import load_dotenv
from types import SimpleNamespace

# Local modules
from tools import TOOLS, run_tool
from utilities.utilities import log



load_dotenv() #by default looks for .env file

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

messages = []

# Safety limit: the max number of model rounds for ONE user question
MAX_STEPS = 5

messages.append(
    {
        "role" : "system",
        "content": (
                     "You are a helpful, humble assistant for Zorvex Technologies employees. "
        "Answer general questions (programming, science, advice) from your own knowledge. "
        "Use get_current_time, get_city_weather and get_user_city only for the current time, the weather, or the user's city. "
        "For ANY question about Zorvex policies, benefits, leave, medical cover, HR, hiring, tech processes, incident reports or travel expenses, "
        "you MUST first call search_knowledge_base. "
        "Answer company questions ONLY from the text that search_knowledge_base returns. Do not use outside knowledge for company facts. "
        "After the answer, cite the source like (leave_policy.txt #3). "
        "If the returned text does not contain the answer, say exactly: I could not find this in the knowledge base. "
        "Keep answers under 100 words."
                )
    }
)

def stream_chat(history):
    stream = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=history,
            tools=TOOLS,
            stream=True,
        )

    full_response = ""
    calls = {}
    label_printed = False

    #Streaming started
    try:
        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            #1. Content Streaming : Do we have message (content) from the LLM
            if delta.content:
                if not label_printed:
                    print("🤖 Assistant: ", end="", flush=True)
                    label_printed = True
                print(delta.content, end="", flush=True)
                full_response += delta.content

            #2. Tool Calls
            for tc in (delta.tool_calls or []):
                obj = calls.setdefault(
                    tc.index,
                    SimpleNamespace(id=None, function=SimpleNamespace(name="", arguments="")),
                )
                if tc.id:
                    obj.id = tc.id
                if tc.function and tc.function.name:
                    obj.function.name += tc.function.name
                if tc.function and tc.function.arguments:
                    obj.function.arguments += tc.function.arguments

    except KeyboardInterrupt:
        print("\n {Stopped By You}")
        calls = {}
    
    if label_printed:
        print()  # Move to the next line after the assistant's response

    calls_list = []
    for key in sorted(calls):
        calls_list.append(calls[key])
    
    return full_response, calls_list


def build_tool_calls_payload(tool_calls):
    """
    Converts our collected tool calls into the dict format
    that the API expects inside an assistant message.
    """

    payload = []
    for tool_call in tool_calls:
        tool_call_dict = {
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            },
        }
        payload.append(tool_call_dict)

    return payload
    

# Chat loop starts from here
while True:

    user_input = input("\n👦🏻 Shubhanshu: ")
    
    if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
        break

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    # Chained Tool Calling
    for step in range(MAX_STEPS):
        full_response, tool_calls = stream_chat(messages)

        #msg = response.choices[0].message

        if not tool_calls:
            break

        log(f"Step {step + 1}: model requested {len(tool_calls)} tool calls")

        messages.append({
            "role": "assistant",
            "content": full_response,
            "tool_calls": build_tool_calls_payload(tool_calls)
        })

        for tool_call in tool_calls:
            result = run_tool(tool_call)
            messages.append({
                "role": "tool",
                "tool_call_id" : tool_call.id,
                "content" : str(result),
            })

    else:
        # Ran out of steps: The model never gave the final answer
        fallback = "Sorry, I could not finish this within the step limit."
        messages.append({
            "role": "assistant",
            "content": fallback
        })
        print("🤖 Assistant: " + fallback)
        continue

    messages.append({
            "role": "assistant",
            "content": full_response
    })