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
    get_driver_vehicle_assignments 
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
        
    else:
        state["answer"] = "I couldn't understand the request."

    return state

def documentation_node(state: AgentState):

    # First try deterministic JSON match
#     match = match_documentation(state["question"])

#     if match:

#         state["answer"] = f"""
# Method: {match['method']}
# Endpoint: {match['endpoint']}
# Description: {match['description']}
# """

#         return state

    # If JSON lookup fails → semantic vector search
    # result = semantic_doc_search(state["question"])

    # if result:
    #     state["answer"] = result
    #     print("This is from vector db")
    # else:
    #     state["answer"] = "Documentation not found."

    # return state
    query = state["question"].lower()

    docs = semantic_doc_search(query)

    if not docs:
        return {"answer": "No documentation found for this query."}

    # determine operation from query
    operation = None

    if "create" in query:
        operation = "create"
    elif "update" in query:
        operation = "update"
    elif "delete" in query:
        operation = "delete"
    elif "list" in query or "get" in query:
        operation = "list"

    # filter docs by operation keyword
    if operation:
        docs = [d for d in docs if operation in d.metadata.get("operation", "")]

    # fallback if filtering removed everything
    if not docs:
        docs = semantic_doc_search(query)

    doc = docs[0]

    method = doc.metadata.get("method", "")
    endpoint = doc.metadata.get("endpoint", "")

    operation = doc.metadata.get("operation", "")
    method = doc.metadata.get("method", "")
    endpoint = doc.metadata.get("endpoint", "")
    text = doc.page_content

    # endpoint question
    if "endpoint" in query:
        answer = f"Endpoint: {endpoint}"

    # method question
    elif "method" in query or "http method" in query:
        answer = f"HTTP Method: {method}"

    # parameters question
    elif "parameter" in query or "field" in query:

        params = []

        for doc in docs:
            text = doc.page_content

            if "Required Parameters" in text or "Body Fields" in text:

                lines = text.split("\n")

                capture = False

                for line in lines:

                    line = line.strip()

                    if (
                        line.startswith("Required Parameters")
                        or line.startswith("Optional Parameters")
                        or line.startswith("Query Parameters")
                        or line.startswith("Body Fields")
                    ):
                        capture = True
                        continue

                    if capture:
                        if not line or line.startswith("API Operation"):
                            continue

                        if line != "None":
                            params.append(line)

        if params:
            return {"answer": "Parameters:\n" + "\n".join(params)}

        return {"answer": "No parameters available."}

    # default short answer
    else:
        answer = f"""
API: {operation}
Method: {method}
Endpoint: {endpoint}
"""
        
    for d in docs:
        print(d.page_content)

    return {"answer": answer.strip()}



# BUILD GRAPH
builder = StateGraph(AgentState)

builder.add_node("classify_node", classify_node)
builder.add_node("api_node", api_node)
builder.add_node("documentation_node", documentation_node)

builder.set_entry_point("classify_node")

builder.add_conditional_edges(
    "classify_node",
    route_decision,
    {
        "api_node": "api_node",
        "documentation_node": "documentation_node"
    }
)

builder.add_edge("api_node", END)
builder.add_edge("documentation_node", END)

graph = builder.compile()
