# ciklum-agentic
A durable, resilient multi-agent execution framework built with Python and Temporal. Features structured telemetry tracing and a runtime containment model that sandboxes untrusted tool executions using network-isolated gVisor/Docker containers.


# Secure Multi-Agent Orchestration Engine (`agenticai`)

This project is a resilient framework that lets multiple AI agents work together to solve problems. It uses **Temporal** to manage the workflow steps so they never crash, and **Docker** to run any AI-generated code inside a secure, locked-down sandbox.

---

## How it Works & The Security Model

When an LLM (like GPT-4 or Claude) writes code to solve a problem, **we cannot trust that code**. It could contain bugs, infinite loops, or malicious scripts. To handle this safely, we split the project into two zones:

1. **The Trusted Worker (Host):** This is our main Python app. It talks to the LLM APIs and manages the steps. It has full internet access.
2. **The Untrusted Sandbox (The Container):** When the AI wants to run code, the Worker boots up a temporary Docker container to run it. 

### Our 3 Security Guardrails:
* **No Network Access (`--net=none`):** The container has no internet and no connection to our local network. It can't download malware or upload our private data.
* **Strict Memory Limits (`--memory=128m`):** The container is capped at 128MB of RAM. If the AI writes code with an infinite loop or a memory leak, it won't crash our main server.
* **gVisor Core (`--runtime=runsc`):** This adds an extra protective layer around the container, blocking the sandboxed code from interacting directly with our main host operating system.

---

## Why We Use Temporal (Resilience & Retries)

If you run an agent system using a standard Python script and your server blinks or crashes, you lose the entire agent run. **Temporal solves this completely.**

* **Crash Proof:** Temporal saves every single step to a database log. If our server loses power mid-run, another server takes over instantly and picks up right where it left off.
* **Safe Failure Handling:** If the AI writes broken code that crashes the Docker container, our main app doesn't crash. Temporal catches the error safely inside that specific step.
* **Automatic Retries:** If a step fails because an LLM API timed out or our server was busy, Temporal automatically retries the step using a smart backoff timer (waiting 2s, then 4s, then 8s) before giving up.
* **Hard Timeouts:** We put a strict 15-second timeout on the code runner. If the AI's code hangs, we forcefully kill the container so it doesn't waste resources.

---

## Monitoring & Tracing

We have built-in logging hooks (`emit_langfuse_trace`) that act like a flight data recorder for our agents:
* It logs exactly what the **Planner Agent** decided to do.
* It tracks the exact code sent to the **Sandbox**.
* It logs how the **Critic Agent** graded the output.

This makes it incredibly easy to debug exactly why an agent succeeded or failed a specific task.

---

## Running it Locally :

1. **Start the Temporal Server** (Runs the background engine):
   ```bash
   docker run --rm -d --name temporal-admin -p 7233:7233 -p 8233:8233 temporalio/auto-setup:latest

## Pre-requisites

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


# Starts the background worker that runs the agents
python agentic_worker.py

# Starts the FastAPI web server
python app.py

## Agent Run Test

curl -X POST http://localhost:8080/api/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Calculate factorial of 5"}'