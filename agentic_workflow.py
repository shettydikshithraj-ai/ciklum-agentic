import subprocess
from datetime import timedelta
from temporalio import workflow, activity

def emit_langfuse_trace(node_name: str, type_str: str, payload: str):
    print(f"[LANGFUSE-TRACE] Node: {node_name} | Type: {type_str} | Payload Length: {len(payload)}")

@activity.defn
async def call_planner_agent(prompt: str) -> str:
    emit_langfuse_trace("planner-agent", "llm-generation", prompt)
    return "import math; print(math.factorial(5))"

@activity.defn
async def execute_in_sandbox(untrusted_code: str) -> str:
    emit_langfuse_trace("sandbox-executor", "untrusted-exec", untrusted_code)
    
    # Secure sandbox containment
    docker_cmd = [
        "docker", "run", "--rm",
        "--runtime=runsc",
        "--net=none",
        "--memory=128m",
        "python:3.11-slim",
        "python", "-c", untrusted_code
    ]
    
    try:
        result = subprocess.run(
            docker_cmd, 
            capture_output=True, 
            text=True, 
            timeout=15
        )
        if result.returncode != 0:
            raise RuntimeError(f"Sandbox execution faulted: {result.stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("Sandbox execution exceeded allocated execution time limits.")

@activity.defn
async def call_critic_agent(execution_result: str) -> str:
    emit_langfuse_trace("critic-agent", "llm-evaluation", execution_result)
    return f"Validated Result: {execution_result}"

@workflow.defn
class MultiAgentWorkflow:
    @workflow.run
    async def run(self, prompt: str) -> dict:
        untrusted_code = await workflow.execute_activity(
            call_planner_agent,
            prompt,
            start_to_close_timeout=timedelta(seconds=60)
        )

        try:
            execution_output = await workflow.execute_activity(
                execute_in_sandbox,
                untrusted_code,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=workflow.RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    backoff_coefficient=2.0,
                    maximum_attempts=3
                )
            )
        except Exception as e:
            return {"status": "SANDBOX_CRASHED", "error": str(e)}

        final_verdict = await workflow.execute_activity(
            call_critic_agent,
            execution_output,
            start_to_close_timeout=timedelta(seconds=60)
        )

        return {"status": "COMPLETED", "result": final_verdict}