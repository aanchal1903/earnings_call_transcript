"""
src/client/earnings_a2a_client.py

A standalone A2A client for testing the Earnings Call Transcript Agent.
This client manages conversation state (context_id) to support multi-turn
interactions and proper A2A protocol communication.
"""
import asyncio
import json
import os
import traceback
from uuid import uuid4
from typing import Optional, Dict, Any

import click
import httpx
import logging

from a2a.client import A2AClient
from a2a.types import (
    SendMessageRequest, SendMessageSuccessResponse,
    GetTaskRequest, TaskQueryParams, GetTaskSuccessResponse,
    MessageSendParams, Message, TextPart, Part,
    Task, TaskState, JSONRPCErrorResponse
)

SESSION_FILE = ".earnings_transcript_session.json"

logger = logging.getLogger(__name__)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s"
    )

def load_session_ids() -> tuple[Optional[str], Optional[str]]:
    """Load saved session IDs from file."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                return data.get("task_id"), data.get("context_id")
        except Exception as e:
            logger.warning(f"Failed to load session file: {e}")
    return None, None

def save_session_ids(task_id: str, context_id: str) -> None:
    """Save session IDs to file for persistence."""
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({"task_id": task_id, "context_id": context_id}, f)
    except Exception as e:
        logger.error(f"Failed to save session file: {e}")

def clear_session_ids() -> None:
    """Clear saved session IDs."""
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
            logger.info("Session cleared.")
        except Exception as e:
            logger.error(f"Failed to clear session file: {e}")

def build_message_payload(text: str, user_id: str, task_id=None, context_id=None) -> Dict[str, Any]:
    """Build A2A message payload."""
    parts = [Part(root=TextPart(text=text))]
    metadata = {"user_id": user_id}
    msg_dict = {
        "role": "user",
        "parts": parts,
        "messageId": uuid4().hex,
        "metadata": metadata,
    }
    if task_id:
        msg_dict["taskId"] = task_id
    if context_id:
        msg_dict["contextId"] = context_id
    return {"message": Message.model_validate(msg_dict)}

async def poll_for_final_task(client: A2AClient, task_id: str, context_id: str) -> Optional[Task]:
    """Poll the task until completion and show progress updates."""
    logger.info(f"Polling task {task_id} for completion.")
    last_text = ""
    
    for _ in range(300):  # 5-minute timeout (earnings calls can take time to scrape)
        await asyncio.sleep(1)
        try:
            request = GetTaskRequest(id=uuid4().hex, params=TaskQueryParams(id=task_id))
            response = await client.get_task(request)

            if isinstance(response.root, JSONRPCErrorResponse):
                logger.error(f"RPC error: {response.root.error.message}")
                return None

            if not isinstance(response.root, GetTaskSuccessResponse):
                logger.error(f"Unexpected response type: {type(response.root)}")
                return None

            task = response.root.result
            
            if task.status.state == TaskState.working:
                msg = task.status.message
                if msg and msg.parts:
                    text = msg.parts[0].root.text
                    if text and text != last_text:
                        print(f"🔄 Agent: {text}")
                        last_text = text

            elif task.status.state in {TaskState.completed, TaskState.failed, TaskState.canceled}:
                return task

        except httpx.ReadTimeout:
            logger.warning(f"Timeout polling task {task_id}")
        except Exception as e:
            logger.error(f"Polling error: {e}", exc_info=True)
            return None
            
    logger.warning(f"Polling timed out for task {task_id}")
    return None

async def interactive_loop(client: A2AClient, user_id: str) -> None:
    """Interactive loop for chatting with the earnings call transcript agent."""
    print("🎯 Earnings Call Transcript Agent - Interactive Client")
    print("=" * 60)
    print(f"Connected as user: {user_id}")
    print()
    print("💡 Example queries:")
    print("  • Get Apple's Q1 2024 earnings call transcript")
    print("  • Search for 'iPhone' in Microsoft's latest earnings call")
    print("  • List available transcripts for Tesla")
    print("  • What did Amazon's CEO say about AWS growth?")
    print("  • Who were the analysts asking questions in Google's Q4 2023 call?")
    print()
    print("Commands:")
    print("  • Type 'exit' or 'quit' to exit")
    print("  • Type '/reset' to start a new session")
    print("  • Type '/help' to see examples")
    print()

    current_task_id, current_context_id = load_session_ids()

    if current_task_id and current_context_id:
        print(f"📝 Restored session: task_id={current_task_id[:8]}..., context_id={current_context_id[:8]}...")
        print()

    while True:
        try:
            query = input("🗣️  You: ").strip()
            
            if not query:
                continue
                
            if query.lower() in {"exit", "quit"}:
                print("👋 Goodbye!")
                break
                
            if query == "/reset":
                clear_session_ids()
                current_task_id = current_context_id = None
                print("🔄 Session reset. Starting fresh conversation.\n")
                continue
                
            if query == "/help":
                print("\n💡 Try these example queries:")
                print("  • Get me Apple's Q1 2024 earnings call transcript")
                print("  • Search for mentions of 'artificial intelligence' in Microsoft's Q4 2023 call")
                print("  • What did Tesla's CEO say about production targets?")
                print("  • List all available transcripts for Google")
                print("  • Who were the analysts in Amazon's latest earnings call?")
                print("  • Validate ticker symbol NVDA")
                print()
                continue

            # Build and send message
            payload = build_message_payload(query, user_id, current_task_id, current_context_id)
            send_req = SendMessageRequest(id=uuid4().hex, params=MessageSendParams(message=payload["message"]))
            
            print("⏳ Sending message to agent...")
            response = await client.send_message(send_req)

            if isinstance(response.root, JSONRPCErrorResponse):
                print(f"❌ Send error: {response.root.error.message}")
                clear_session_ids()
                current_task_id = current_context_id = None
                continue

            if not isinstance(response.root, SendMessageSuccessResponse):
                print(f"❌ Unexpected response type: {type(response.root)}")
                continue

            task = response.root.result
            current_task_id, current_context_id = task.id, task.contextId
            save_session_ids(current_task_id, current_context_id)

            print(f"📋 Task created: {current_task_id[:8]}...")
            
            # Poll for completion
            final = await poll_for_final_task(client, current_task_id, current_context_id)
            
            if final and final.status.message:
                print("\n" + "=" * 60)
                print("🤖 Final Response:")
                print("=" * 60)
                parts = final.status.message.parts
                texts = [p.root.text for p in parts if isinstance(p.root, TextPart) and p.root.text]
                full_response = "".join(texts).strip()
                print(full_response)
                print("=" * 60)
                
                # Show task completion status
                if final.status.state == TaskState.completed:
                    print("✅ Task completed successfully")
                elif final.status.state == TaskState.failed:
                    print("❌ Task failed")
                elif final.status.state == TaskState.canceled:
                    print("⚠️ Task was canceled")
                    
            elif final:
                print(f"⚠️ Task {final.status.state.value}: No message returned.")
            else:
                print("❌ Agent did not respond or timed out.")
                
            print()  # Add spacing between interactions

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            traceback.print_exc()
            print()

# @click.command()
# @click.option(
#     "--agent-url", 
#     default="http://localhost:8080", 
#     show_default=True, 
#     help="Earnings Call Transcript Agent URL"
# )
# @click.option(
#     "--user-id", 
#     default=f"earnings-user-{uuid4().hex[:6]}", 
#     show_default=True, 
#     help="User ID for session"
# )
# def cli_main(agent_url: str, user_id: str) -> None:
#     """CLI entry point for the earnings call transcript agent client."""
#     asyncio.run(run_client_interaction(agent_url, user_id))

# In your transcript_a2a_client.py, change the default port:

@click.command()
@click.option(
    "--agent-url", 
    default="http://localhost:8081",  # Changed to match A2A server port
    show_default=True, 
    help="Earnings Call Transcript Agent URL"
)
@click.option(
    "--user-id", 
    default=f"earnings-user-{uuid4().hex[:6]}", 
    show_default=True, 
    help="User ID for session"
)
def cli_main(agent_url: str, user_id: str) -> None:
    """CLI entry point for the earnings call transcript agent client."""
    asyncio.run(run_client_interaction(agent_url, user_id))

async def run_client_interaction(agent_url: str, user_id: str) -> None:
    """Run the client interaction with proper error handling."""
    logger.info(f"Connecting to {agent_url} as {user_id}")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as session:  # 5 minute timeout for scraping
            print(f"🔗 Connecting to earnings call transcript agent at {agent_url}")
            client = await A2AClient.get_client_from_agent_card_url(session, agent_url)
            print("✅ Connected successfully!")
            print()
            await interactive_loop(client, user_id)
            
    except httpx.ConnectError:
        print(f"❌ Cannot connect to agent at {agent_url}")
        print("Make sure your agent is running:")
        print("  python run_backend.py  # Terminal 1")
        print("  python run_mcp.py      # Terminal 2") 
        print("  python run_a2a.py      # Terminal 3")
        
    except Exception as exc:
        print(f"❌ Startup error: {exc}")
        traceback.print_exc()

if __name__ == "__main__":
    cli_main()