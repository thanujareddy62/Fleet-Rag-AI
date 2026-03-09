from flask import Flask, render_template, request
from agent.memory import ConversationMemory
from agent.langgraph_agent import agent_workflow

app = Flask(__name__)

memory = ConversationMemory()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        question = request.form["question"]
        answer = agent_workflow(question)
        memory.add(question, answer)

    return render_template("index.html", history=memory.history)


if __name__ == "__main__":
    app.run(debug=True)