import json, re
from typing import TypedDict
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from agent.doc_vector_retriever import semantic_doc_search
from agent.entity_extractors.driver_extractor import extract_driver_data
from langchain.tools import Tool
from langchain.agents import initialize_agent

# from agent.documentation import match_documentation
from agent.entity_extractors.vehicle_extractor import detect_vehicle_id
from agent.tools import (
    get_all_drivers,
    get_driver_count,
    get_all_vehicles,
    get_vehicle_count,
    get_routes_today,
    get_route_count,
    get_driver_vehicle_assignments_count,
    get_driver_vehicle_assignments,
    fleet_summary
)

from agent.intent_classifier import detect_intent_semantic
import re

def extract_driver_name(question):

    match = re.search(r"to\s+([A-Za-z\s\.]+)", question)

    if match:
        return match.group(1).strip()

    return None

# STATE
class AgentState(TypedDict):
    question: str
    intent: str
    answer: str
    history: list

# GLOBAL CHAT MEMORY
CHAT_HISTORY = []

# ENTRY FUNCTION
def agent_workflow(question: str):

    global CHAT_HISTORY

    result = graph.invoke({
        "question": question,
        "intent": "",
        "answer": "",
        "history": CHAT_HISTORY
    })
    # store conversation
    CHAT_HISTORY.append({
        "question": question,
        "answer": result["answer"]
    })

    print("\n----- Conversation Memory -----")
    print(CHAT_HISTORY)
    print("--------------------------------")

    return result["answer"]


# NODES
def classify_node(state: AgentState):

    state["intent"] = detect_intent(state["question"])
    print("Detected Intent:", state["intent"])

    return state


# INTENT DETECTION 
def detect_intent(question):
    return detect_intent_semantic(question)


# ROUTER
def route_decision(state):

    q = state["question"].lower()

    # detect vehicle numbers
    vehicle = detect_vehicle_id(state["question"])

    if vehicle:
        print("Routing → reasoning_node (vehicle detected)")
        return "reasoning_node"

    #API Troubleshooting
    if any(word in q for word in ["401","404","400","403","error","api error","unauthorized","bad request","forbidden"]):
        print("Routing → troubleshooting_node")
        return "troubleshooting_node"

    # API request generator
    if any(word in q for word in [
        "generate api request",
        "generate request",
        "example request",
        "request body",
        "curl request",
        "python request"
    ]):
        print("Routing → request_generator_node")
        return "request_generator_node"

    # documentation-related questions
    documentation_keywords = [
        "api",
        "endpoint",
        "method",
        "documentation",
        "parameter",
        "parameters",
        "field",
        "fields",
        "example",
        "request"
    ]

    # Force documentation node if query asks about API structure
    if any(word in q for word in documentation_keywords):
        print("Routing → documentation_node")
        return "documentation_node"

    # fallback based on semantic intent
    if state["intent"] in ["documentation", "unknown"]:
        print("Routing → documentation_node (intent fallback)")
        return "documentation_node"

    # strong API intents only
    strong_api_intents = [
        "list drivers",
        "count drivers",
        "list vehicles",
        "count vehicles",
        "routes today",
        "count routes",
        "count assignments",
        "fleet summary",
        "list routes",
        "show assignments"
    ]

    if state["intent"] in strong_api_intents:
        print("Routing → api_node")
        return "api_node"

    # everything else → reasoning
    print("Routing → reasoning_node")
    return "reasoning_node"


def api_node(state: AgentState):

    intent = state["intent"]
    q = state["question"].lower()

    # 🔹 Use conversation memory if driver not mentioned
    if "vehicle" in q and "driver" not in q:

        if state["history"]:
            last_q = state["history"][-1]["question"].lower()

            if "driver" in last_q:
                print("Using conversation context")

    # Detect driver name in question
    name = extract_driver_name(state["question"])

    if name and "vehicle" in q:
        intent = "driver vehicle lookup"

    if intent == "list drivers":
        state["answer"] = get_all_drivers()

    elif intent == "count drivers":
        state["answer"] = get_driver_count()

    elif intent == "list vehicles":
        state["answer"] = get_all_vehicles()

    elif intent == "count vehicles":
        state["answer"] = get_vehicle_count()

    elif intent == "routes today":
        state["answer"] = get_routes_today()

    elif intent == "count routes":
        state["answer"] = get_route_count() 

    elif intent == "count assignments":
        state["answer"] = get_driver_vehicle_assignments_count()

    elif intent == "list assignments":
        state["answer"] = get_driver_vehicle_assignments()

    elif intent == "driver vehicle lookup":

        name = extract_driver_name(state["question"])

        if not name:
            state["answer"] = "Driver name not detected."
            return state

        assignments = get_driver_vehicle_assignments()

        lines = assignments.split("\n")

        result = []

        for line in lines:
            if name.lower() in line.lower():
                result.append(line)

        # remove duplicates
        result = list(dict.fromkeys(result))

        if result:
            state["answer"] = "\n".join(result)
        else:
            state["answer"] = f"No vehicle assigned to {name}."

        return state

    elif intent == "fleet summary":
        state["answer"] = fleet_summary()
        
    else:
        state["answer"] = "I couldn't understand the request."

    return state

def documentation_node(state: AgentState):

    query = state["question"].lower()

    docs = semantic_doc_search(query)

    if not docs:
        return {"answer": "Documentation not found."}

    doc = docs[0]

    operation = doc.metadata.get("operation", "")
    method = doc.metadata.get("method", "")
    endpoint = doc.metadata.get("endpoint", "")

    # endpoint question
    if "endpoint" in query:
        return {"answer": f"Endpoint: {endpoint}"}

    # method question
    if "method" in query:
        return {"answer": f"HTTP Method: {method}"}

    # parameters question
    if "parameter" in query:

        params = []

        for d in docs:

            lines = d.page_content.split("\n")

            capture = False

            for line in lines:

                line = line.strip()

                if line.startswith(("Required Parameters", "Optional Parameters", "Query Parameters", "Body Fields")):
                    capture = True
                    continue

                if capture:
                    if not line or line.startswith("API Operation"):
                        capture = False
                        continue

                    if line != "None":
                        params.append(line)

        params = list(dict.fromkeys(params))

        if params:
            return {"answer": "Parameters:\n" + "\n".join(params)}

        return {"answer": "No parameters available."}

    print("This is from vectordb")
    return {
        "answer": f"API: {operation}\nMethod: {method}\nEndpoint: {endpoint}"
    }


def extract_driver_details(text):

    name = None
    username = None
    password = None

    name_match = re.search(r"named\s+([A-Za-z]+)", text)
    username_match = re.search(r"username\s+([A-Za-z0-9_]+)", text)
    password_match = re.search(r"password\s+([A-Za-z0-9_]+)", text)

    if name_match:
        name = name_match.group(1)

    if username_match:
        username = username_match.group(1)

    if password_match:
        password = password_match.group(1)

    return {
        "name": name,
        "username": username,
        "password": password
    }

def request_generator_node(state: AgentState):

    query = state["question"]

    docs = semantic_doc_search(query)

    if not docs:
        return {"answer": "API documentation not found."}

    doc = docs[0]

    operation = doc.metadata.get("operation", "")
    method = doc.metadata.get("method", "")
    endpoint = doc.metadata.get("endpoint", "")

    required_params = doc.metadata.get("required_parameters", [])
    optional_params = doc.metadata.get("optional_parameters", [])
    query_params = doc.metadata.get("query_parameters", [])
    body_fields = doc.metadata.get("body_fields", [])

    body = {}
    query_dict = {}

    # 🔹 Extract driver values from natural language
    driver_data = extract_driver_data(query)

    for k, v in driver_data.items():
        if v:
            body[k] = v

    # Required parameters
    if isinstance(required_params, dict):
        for k in required_params.keys():
            if k not in body:
                body[k] = "value"
    else:
        for p in required_params:
            if p not in body:
                body[p] = "value"

    # Optional parameters
    if isinstance(optional_params, list):
        for p in optional_params:
            if p not in body:
                body[p] = "optional_value"

    # Body fields
    if isinstance(body_fields, list):
        for p in body_fields:
            if p not in body:
                body[p] = "value"

    # Query parameters
    if isinstance(query_params, list):
        for p in query_params:
            if isinstance(p, dict):
                name = p.get("name")
                if name:
                    query_dict[name] = "value"

    body_json = json.dumps(body, indent=2)
    query_json = json.dumps(query_dict, indent=2)

    # cURL request
    curl_cmd = f"""curl -X {method} "{endpoint}" \\
-H "Authorization: Bearer YOUR_API_TOKEN" \\
-H "Content-Type: application/json" \\
-d '{body_json}'
"""

    # Python request
    python_request = f"""
import requests

url = "{endpoint}"

headers = {{
    "Authorization": "Bearer YOUR_API_TOKEN",
    "Content-Type": "application/json"
}}

payload = {body_json}

response = requests.{method.lower()}(url, headers=headers, json=payload)

print(response.status_code)
print(response.json())
"""

    answer = f"""
🔹 API Operation: {operation}

Endpoint
{method} {endpoint}

--------------------------------------------------

Query Parameters
{query_json}

--------------------------------------------------

Request Body
{body_json}

--------------------------------------------------

cURL Example
{curl_cmd}

--------------------------------------------------

Python Example
{python_request}

--------------------------------------------------

Postman Request

Method: {method}
URL: {endpoint}

Body (raw JSON)
{body_json}
"""

    return {"answer": answer.strip()}

#API trouble shooting node
def troubleshooting_node(state: AgentState):

    q = state["question"].lower()

    if "401" in q:
        answer = """
401 Unauthorized usually occurs when:

• API token is invalid
• Authorization header is missing
• Token expired
• Incorrect API key used
"""

    elif "404" in q:
        answer = """
404 Not Found usually occurs when:

• Incorrect API endpoint
• Resource ID does not exist
• Wrong API version
"""

    elif "400" in q:
        answer = """
400 Bad Request usually occurs when:

• Missing required parameters
• Incorrect JSON body format
• Invalid parameter values
"""

    elif "403" in q:
        answer = """
403 Forbidden usually occurs when:

• Insufficient API permissions
• Token does not have required scopes
"""

    else:
        answer = "Unable to determine the error cause."

    return {"answer": answer}


def reasoning_node(state: AgentState):

    # question = state["question"]

    # llm = ChatOllama(
    #     model="llama3",
    #     temperature=0
    # )

    # tools = [
    #     Tool(
    #         name="get_all_drivers",
    #         func=lambda _: get_all_drivers(),
    #         description="Returns list of drivers"
    #     ),
    #     Tool(
    #         name="get_all_vehicles",
    #         func=lambda _: get_all_vehicles(),
    #         description="Returns list of vehicles"
    #     ),
    #     Tool(
    #         name="get_driver_vehicle_assignments",
    #         func=lambda _: get_driver_vehicle_assignments(),
    #         description="Returns mapping between drivers and vehicles"
    #     ),
    #     Tool(
    #         name="get_routes_today",
    #         func=lambda _: get_routes_today(),
    #         description="Returns today's routes"
    #     )
    # ]

    # agent = initialize_agent(
    #     tools,
    #     llm,
    #     agent="zero-shot-react-description",
    #     verbose=False
    # )

    # result = agent.invoke(question)

    # return {"answer": result["output"]}
    question = state["question"]

    # Initialize local LLM
    llm = ChatOllama(
        model="llama3",
        temperature=0
    )

    vehicle = detect_vehicle_id(question)

    if vehicle:
        data = get_driver_vehicle_assignments()

        for line in data.split("\n"):
            if vehicle in line:
                return {"answer": line}

    try:
        # Retrieve real fleet data using your existing tools
        drivers = get_all_drivers()
        vehicles = get_all_vehicles()
        assignments = get_driver_vehicle_assignments()
        routes = get_routes_today()

        # Create reasoning prompt
        prompt = f"""
You are a fleet assistant.

Use ONLY the provided fleet data to answer the question.
Do NOT guess or hallucinate information.

Fleet Data:

Drivers:
{drivers}

Vehicles:
{vehicles}

Driver-Vehicle Assignments:
{assignments}

Routes:
{routes}

User Question:
{question}

Answer clearly and accurately using the fleet data above.
If the information is not present, say:
"I could not find this information in the fleet data."
"""

        response = llm.invoke(prompt)

        return {"answer": response.content}

    except Exception as e:
        return {"answer": f"Reasoning error: {str(e)}"}


# BUILD GRAPH
builder = StateGraph(AgentState)

builder.add_node("classify_node", classify_node)
builder.add_node("api_node", api_node)
builder.add_node("documentation_node", documentation_node)
builder.add_node("request_generator_node", request_generator_node)
builder.add_node("troubleshooting_node", troubleshooting_node)
builder.add_node("reasoning_node", reasoning_node)

builder.set_entry_point("classify_node")

builder.add_conditional_edges(
    "classify_node",
    route_decision,
    {
        "api_node": "api_node",
        "documentation_node": "documentation_node",
        "request_generator_node": "request_generator_node",
        "troubleshooting_node": "troubleshooting_node",
        "reasoning_node": "reasoning_node"
    }
)

builder.add_edge("api_node", END)
builder.add_edge("documentation_node", END)
builder.add_edge("request_generator_node", END)
builder.add_edge("troubleshooting_node", END)
builder.add_edge("reasoning_node", END)

graph = builder.compile()
