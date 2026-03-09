from sentence_transformers import SentenceTransformer, util
import torch

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Intent examples
INTENT_EXAMPLES = {
    "list drivers": [
        "show drivers",
        "list drivers",
        "names of drivers",
        "what drivers exist",
        "give me drivers",
        "display drivers",
        "drivers list"
    ],
    "fleet summary" : [
        "give fleet summary"
    ],

    "count drivers": [
        "how many drivers",
        "driver count",
        "total drivers"
    ],

    "list vehicles": [
        "show vehicles",
        "list vehicles",
        "vehicle names",
        "display vehicles",
        "what vehicles exist",
        "fleet vehicles"
    ],

    "count vehicles": [
        "how many vehicles",
        "vehicle count",
        "total vehicles"
    ],

    "list assignments": [
        "show driver vehicle assignments",
        "list assignments",
        "which drivers are assigned to vehicles",
        "show assignments",
        "list assignments",
        "driver vehicle assignments",
        "assignment list",
        "who is assigned to which vehicle"
    ],

    "count assignments": [
        "how many assignments",
        "assignment count",
        "total assignments"
    ],

    "count routes": [
        "how many routes",
        "route count",
        "total routes"
    ],

    "documentation": [
        "api endpoint",
        "api method",
        "which endpoint",
        "what endpoint",
        "endpoint for",
        "endpoint to",
        "api endpoint for",
        "how to update driver",
        "documentation for vehicles api",
        "api to remove assignment",
        "endpoint to remove assignment",
        "endpoint to delete assignment",
        "what is the endpoint to delete a driver",
        "delete driver api",
        "remove driver assignment api",
        "how to delete assignment",
        "driver assignment delete endpoint",
        "modify driver api",
        "edit driver endpoint",
        "driver api documentation",
        "vehicle api endpoint",
        "route api documentation",
        "how to create a route",
        "how to add",
        "how to delete",
        "what method updates driver",
        "which method deletes assignment",
        "what http method updates route",
        "What parameters are required to create a driver?",
        "what parameters create driver",
        "example request for routes",
        "what fields driver api returns",
        "What parameters are required"
    ]
}

# Precompute embeddings, store vector embeddings for each intent's example sentences.
intent_embeddings = {}

for intent, examples in INTENT_EXAMPLES.items():
    intent_embeddings[intent] = model.encode(examples)


def detect_intent_semantic(question):

    q_embedding = model.encode(question)

    best_intent = None
    best_score = -1

    for intent, embeddings in intent_embeddings.items():
        #Cosine similarity measures how similar two vectors are.
        scores = util.cos_sim(q_embedding, embeddings)

        score = torch.max(scores).item()

        if score > best_score:
            best_score = score
            best_intent = intent

    #if similarity is too low, the system assumes the question is about documentation
    if best_score < 0.35:
        return "documentation"

    return best_intent