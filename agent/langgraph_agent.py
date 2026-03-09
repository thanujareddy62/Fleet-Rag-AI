import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from agent.doc_vector_retriever import semantic_doc_search

from agent.documentation import match_documentation
from agent.tools import (
    get_all_drivers,
    get_driver_count,
    get_all_vehicles,
    get_vehicle_by_driver_name,
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

    match = re.search(r"is\s+([A-Za-z\.]+)", question)

    if match:
        return match.group(1)

    return None

# STATE
class AgentState(TypedDict):
    question: str
    intent: str
    answer: str


# ENTRY FUNCTION
def agent_workflow(question: str):

    result = graph.invoke({
        "question": question,
        "intent": "",
        "answer": ""
    })

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

    # API request generator
    if any(word in q for word in [
        "generate api request",
        "generate request",
        "example request",
        "request body",
        "curl request"
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

    return "api_node"


def api_node(state: AgentState):

    intent = state["intent"]

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

        if name:
            state["answer"] = get_vehicle_by_driver_name(name)
        else:
            state["answer"] = "Driver name not detected."

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

    # Required parameters
    if isinstance(required_params, dict):
        for k in required_params.keys():
            body[k] = "value"
    else:
        for p in required_params:
            body[p] = "value"

    # Optional parameters
    if isinstance(optional_params, list):
        for p in optional_params:
            body[p] = "optional_value"

    # Body fields
    if isinstance(body_fields, list):
        for p in body_fields:
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

    answer = f"""
API: {operation}

{method} {endpoint}

Query Parameters:
{query_json}

Request Body:
{body_json}
"""

    return {"answer": answer.strip()}


# BUILD GRAPH
builder = StateGraph(AgentState)

builder.add_node("classify_node", classify_node)
builder.add_node("api_node", api_node)
builder.add_node("documentation_node", documentation_node)
builder.add_node("request_generator_node", request_generator_node)

builder.set_entry_point("classify_node")

builder.add_conditional_edges(
    "classify_node",
    route_decision,
    {
        "api_node": "api_node",
        "documentation_node": "documentation_node",
        "request_generator_node": "request_generator_node"
    }
)

builder.add_edge("api_node", END)
builder.add_edge("documentation_node", END)
builder.add_edge("request_generator_node", END)

graph = builder.compile()
