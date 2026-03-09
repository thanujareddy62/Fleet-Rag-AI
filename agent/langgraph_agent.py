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

    if any(word in q for word in ["api", "endpoint", "method", "documentation"]):
        return "documentation_node"

    if state["intent"] in ["documentation", "unknown"]:
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

    doc = docs[0]

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
    elif "parameter" in query or "fields" in query:

        lines = text.split("\n")

        param_lines = []
        capture = False

        for line in lines:

            if (
                "Required Parameters" in line
                or "Optional Parameters" in line
                or "Query Parameters" in line
                or "Body Fields" in line
            ):
                capture = True
                continue

            if capture:
                if line.strip() == "":
                    break
                param_lines.append(line.strip())

        if param_lines:
            answer = "Parameters:\n" + "\n".join(param_lines)
        else:
            answer = "No parameters available."

    # example request question
    elif "example" in query:
        start = text.find("Example")
        if start != -1:
            answer = text[start:]
        else:
            answer = "No example request available."

    # default short answer
    else:
        answer = f"""
API: {operation}
Method: {method}
Endpoint: {endpoint}
"""

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







# from typing import TypedDict
# from langgraph.graph import StateGraph, END

# from agent.tools import (
#     get_driver_count,
#     get_total_route_count,
#     get_vehicle_count,
#     get_assignment_count,
#     fleet_summary,
#     drivers_without_vehicles,
#     vehicles_without_drivers,
#     routes_without_stops
# )

# from agent.retriever import retrieve_docs


# # -----------------------------
# # 1️⃣ STATE DEFINITION
# # -----------------------------

# class AgentState(TypedDict):
#     question: str
#     intent: str
#     answer: str


# # -----------------------------
# # 2️⃣ INTENT DETECTION
# # -----------------------------

# def detect_intent(question: str):

#     q = question.lower()

#     # 🔹 Documentation priority
#     doc_keywords = [
#         "endpoint",
#         "api",
#         "method",
#         "url",
#         "documentation",
#         "how to",
#         "create",
#         "update",
#         "retrieve"
#     ]

#     if any(word in q for word in doc_keywords):
#         return "documentation"

#     # 🔹 Dashboard
#     if "fleet summary" in q or "dashboard" in q:
#         return "fleet summary"

#     # 🔹 Counts
#     if "how many drivers" in q or "driver count" in q:
#         return "count drivers"

#     if "how many vehicles" in q or "vehicle count" in q:
#         return "count vehicles"

#     if "how many routes" in q or "route count" in q:
#         return "count routes"

#     # 🔹 Anomaly Detection
#     if "drivers without vehicles" in q:
#         return "drivers without vehicles"

#     if "vehicles without drivers" in q:
#         return "vehicles without drivers"

#     if "routes without stops" in q:
#         return "routes without stops"

#     # 🔹 Default fallback
#     return "documentation"


# # -----------------------------
# # 3️⃣ NODES
# # -----------------------------

# def classify_node(state: AgentState):

#     state["intent"] = detect_intent(state["question"])
#     print("Detected Intent:", state["intent"])  # Debug
#     return state


# def api_node(state: AgentState):

#     intent = state["intent"]

#     if intent == "count drivers":
#         state["answer"] = f"Total drivers: {get_driver_count()}"

#     elif intent == "count vehicles":
#         state["answer"] = f"Total vehicles: {get_vehicle_count()}"

#     elif intent == "count routes":
#         state["answer"] = f"Total routes: {get_total_route_count()}"

#     elif intent == "fleet summary":
#         state["answer"] = fleet_summary()

#     elif intent == "drivers without vehicles":
#         state["answer"] = drivers_without_vehicles()

#     elif intent == "vehicles without drivers":
#         state["answer"] = vehicles_without_drivers()

#     elif intent == "routes without stops":
#         state["answer"] = routes_without_stops()

#     else:
#         state["answer"] = "Unsupported API request."

#     return state


# def rag_node(state: AgentState):
#     """
#     Deterministic documentation retrieval.
#     No LLM used.
#     """

#     docs = retrieve_docs(state["question"], k=1)

#     if not docs:
#         state["answer"] = "Information not available in documentation."
#         return state

#     doc = docs[0]
#     state["answer"] = doc.page_content.strip()

#     return state


# # -----------------------------
# # 4️⃣ ROUTING LOGIC
# # -----------------------------

# def route_decision(state: AgentState):

#     if state["intent"] == "documentation":
#         return "rag_node"
#     else:
#         return "api_node"


# # -----------------------------
# # 5️⃣ BUILD GRAPH
# # -----------------------------

# builder = StateGraph(AgentState)

# builder.add_node("classify_node", classify_node)
# builder.add_node("api_node", api_node)
# builder.add_node("rag_node", rag_node)

# builder.set_entry_point("classify_node")

# builder.add_conditional_edges(
#     "classify_node",
#     route_decision,
#     {
#         "api_node": "api_node",
#         "rag_node": "rag_node",
#     },
# )

# builder.add_edge("api_node", END)
# builder.add_edge("rag_node", END)

# graph = builder.compile()


# # -----------------------------
# # 6️⃣ ENTRY FUNCTION
# # -----------------------------

# def agent_workflow(question: str):

#     result = graph.invoke({
#         "question": question,
#         "intent": "",
#         "answer": ""
#     })

#     return result["answer"]




# from typing import TypedDict
# from langgraph.graph import StateGraph, END
# from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

# from agent.tools import (
#     get_all_drivers,
#     get_driver_count,
#     get_all_vehicles,
#     get_vehicle_count,
#     get_routes_today
# )

# from agent.retriever import retrieve_docs

# # -----------------------------
# # 1️⃣ STATE DEFINITION
# # -----------------------------

# class AgentState(TypedDict):
#     question: str
#     intent: str
#     answer: str


# # -----------------------------
# # 2️⃣ MODELS
# # -----------------------------

# intent_classifier = pipeline(
#     "zero-shot-classification",
#     model="facebook/bart-large-mnli"
# )

# model_name = "google/flan-t5-base"

# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# generator = pipeline(
#     "text-generation",   # yes, still this
#     model=model,
#     tokenizer=tokenizer
# )

# INTENTS = [
#     "list drivers",
#     "count drivers",
#     "list vehicles",
#     "count vehicles",
#     "routes today",
#     "documentation question"
# ]

# def detect_intent(question):

#     q = question.lower()

#     # 🔥 Documentation override rule
#     doc_keywords = ["endpoint", "api", "method", "url", "documentation", "how to"]

#     if any(word in q for word in doc_keywords):
#         return "documentation"

#     result = intent_classifier(question, INTENTS)

#     label = result["labels"][0]
#     score = result["scores"][0]

#     if score < 0.60:
#         return "documentation"

#     return label

# # -----------------------------
# # 3️⃣ NODES
# # -----------------------------
# def classify_node(state: AgentState):
#     state["intent"] = detect_intent(state["question"])
#     print("Detected Intent:", state["intent"])  # debug
#     return state


# def api_node(state: AgentState):

#     intent = state["intent"]

#     if intent == "list drivers":
#         state["answer"] = get_all_drivers()

#     elif intent == "count drivers":
#         state["answer"] = get_driver_count()

#     elif intent == "list vehicles":
#         state["answer"] = get_all_vehicles()

#     elif intent == "count vehicles":
#         state["answer"] = get_vehicle_count()

#     elif intent == "routes today":
#         state["answer"] = get_routes_today()

#     return state


# def rag_node(state: AgentState):

#     docs = retrieve_docs(state["question"], k=1)
#     context = "\n".join([doc.page_content for doc in docs])

#     prompt = f"""
# Answer the question using the provided context.

# Context:
# {context}

# Question:
# {state['question']}

# Answer:
# """

#     result = generator(
#         prompt,
#         max_new_tokens=120,
#         do_sample=False,
#         return_full_text=False,
#         eos_token_id=tokenizer.eos_token_id
#     )

#     print("RAW OUTPUT:", result)
#     result = generator(
#     prompt,
#     max_new_tokens=120,
#     do_sample=False,
#     return_full_text=False,
#     eos_token_id=tokenizer.eos_token_id
# )

#     state["answer"] = result[0]["generated_text"].strip()

#     return state


# # -----------------------------
# # 4️⃣ ROUTING LOGIC
# # -----------------------------

# def route_decision(state: AgentState):

#     if state["intent"] == "documentation":
#         return "rag_node"
#     else:
#         return "api_node"


# # -----------------------------
# # 5️⃣ BUILD GRAPH
# # -----------------------------

# builder = StateGraph(AgentState)

# builder.add_node("classify_node", classify_node)
# builder.add_node("api_node", api_node)
# builder.add_node("rag_node", rag_node)

# builder.set_entry_point("classify_node")

# builder.add_conditional_edges(
#     "classify_node",
#     route_decision,
#     {
#         "api_node": "api_node",
#         "rag_node": "rag_node",
#     },
# )

# builder.add_edge("api_node", END)
# builder.add_edge("rag_node", END)

# graph = builder.compile()


# # -----------------------------
# # 6️⃣ ENTRY FUNCTION
# # -----------------------------

# def agent_workflow(question: str):

#     result = graph.invoke({
#         "question": question,
#         "intent": "",
#         "answer": ""
#     })

#     return result["answer"]