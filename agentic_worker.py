import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflow import MultiAgentWorkflow, call_planner_agent, execute_in_sandbox, call_critic_agent

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="multi-agent-task-queue",
        workflows=[MultiAgentWorkflow],
        activities=[call_planner_agent, execute_in_sandbox, call_critic_agent]
    )
    print("🤖 Resilient Worker is active and listening for tasks...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())