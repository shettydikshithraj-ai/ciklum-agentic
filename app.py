from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from temporalio.client import Client
import uuid

app = FastAPI()

class RunRequest(BaseModel):
    prompt: str

@app.post("/api/run")
async def start_run(payload: RunRequest):
    try:
        client = await Client.connect("localhost:7233")
        task_id = f"agent_task_{uuid.uuid4().hex[:8]}"
        
        handle = await client.start_workflow(
            "MultiAgentWorkflow",
            payload.prompt,
            id=f"wf-{task_id}",
            task_queue="multi-agent-task-queue"
        )
        
        return {
            "task_id": task_id,
            "workflow_id": handle.id,
            "run_id": handle.first_execution_run_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)