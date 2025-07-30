"""
agents/earnings_call_transcript_agent/src/earnings_call_transcript_agent/agent_executor.py

Bridges A2A protocol requests to the ADK-based Earnings Call Transcript Agent.
Manages task lifecycle, consumes the agent's event stream to send
progress updates, and returns the final result as A2A artifacts or messages.
This version uses in-memory storage instead of database.
"""

import logging
from uuid import uuid4
from typing import Optional

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Task, TaskState, UnsupportedOperationError
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService  # Changed from DatabaseSessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.genai import types as genai_types
from google.adk.events import Event as ADKEvent

from earnings_call_transcript_agent.agent import earnings_call_transcript_agent 
from config.config import settings

logger = logging.getLogger(__name__)

class EarningsCallTranscriptAgentExecutor(AgentExecutor):
    """
    A2A Executor that handles streaming and in-memory sessions for the
    Earnings Call Transcript ADK agent.
    """
    def __init__(self) -> None:
        super().__init__()
        self.adk_agent_instance = earnings_call_transcript_agent
        self.session_service = InMemorySessionService()  # Changed to in-memory
        self._runner = Runner(
            agent=self.adk_agent_instance,
            app_name=self.adk_agent_instance.name,
            session_service=self.session_service,
            memory_service=InMemoryMemoryService(),
            artifact_service=InMemoryArtifactService(),
        )
        logger.info("EarningsCallTranscriptAgentExecutor initialized with in-memory ADK Runner.")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Handles an incoming A2A execute request by running the ADK agent's
        workflow and streaming the results.

        Args:
            context: The request context containing the user's message and task info.
            event_queue: The queue for sending events back to the client.
        """
        query = context.get_user_input() or "User provided an empty query."
        a2a_task = context.current_task
        user_meta = context.message.metadata or {}
        user_id = str(user_meta.get("user_id", f"earnings_user_{uuid4().hex[:6]}"))
        adk_session_id = context.message.contextId or uuid4().hex
        context.message.contextId = adk_session_id

        if not a2a_task:
            a2a_task = new_task(context.message)
            if not a2a_task.metadata: a2a_task.metadata = {}
            a2a_task.metadata["adk_session_id"] = adk_session_id
            await event_queue.enqueue_event(a2a_task)
        
        updater = TaskUpdater(event_queue, a2a_task.id, adk_session_id)
        logger.info(
            f"Executing A2A Task {a2a_task.id} for Earnings Call Transcript. "
            f"ADK Session: {adk_session_id}, User: {user_id}"
        )
        try:
            # Create session if it doesn't exist (in-memory)
            adk_session = await self._runner.session_service.get_session(
                app_name=self.adk_agent_instance.name, user_id=user_id, session_id=adk_session_id
            )
            if not adk_session:
                await self._runner.session_service.create_session(
                    app_name=self.adk_agent_instance.name, user_id=user_id, session_id=adk_session_id, state={}
                )

            genai_user_message = genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=query)])
            final_adk_event: Optional[ADKEvent] = None
            
            async for adk_event in self._runner.run_async(user_id=user_id, session_id=adk_session_id, new_message=genai_user_message):
                if adk_event.is_final_response():
                    final_adk_event = adk_event
                    continue

                if adk_event.content and adk_event.content.parts:
                    part = adk_event.content.parts[0]
                    thought_text = ""
                    if part.function_call:
                        tool_name = part.function_call.name
                        if tool_name == "get_transcript":
                            thought_text = "Fetching earnings call transcript from the provided URL..."
                        else:
                            thought_text = f"Calling tool: `{tool_name}`..."
                    elif part.function_response:
                        thought_text = f"Tool `{part.function_response.name}` completed."

                    if thought_text:
                        await updater.update_status(
                            TaskState.working,
                            new_agent_text_message(thought_text, adk_session_id, a2a_task.id)
                        )
            
            if not final_adk_event or not final_adk_event.content or not final_adk_event.content.parts:
                raise RuntimeError("Agent workflow completed without a final response.")
            
            final_text = final_adk_event.content.parts[0].text
            await updater.update_status(
                TaskState.completed,
                new_agent_text_message(final_text, adk_session_id, a2a_task.id),
                final=True
            )
            logger.info(f"Task {a2a_task.id} completed successfully.")

        except Exception as e:
            logger.exception(f"Earnings Call Transcript workflow failed for A2A Task {a2a_task.id}: {e}")
            error_message = new_agent_text_message(f"I encountered an error: {str(e)}", adk_session_id, a2a_task.id)
            await updater.update_status(TaskState.failed, error_message, final=True)

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Optional[Task]:
        """ Handles an A2A task cancellation request. """
        task_to_cancel = request.current_task
        if not task_to_cancel:
            raise ServerError(error=UnsupportedOperationError(message="No active task to cancel."))
        
        logger.info(f"Cancelling A2A Task {task_to_cancel.id} for Earnings Call Transcript.")
        updater = TaskUpdater(event_queue, task_to_cancel.id, task_to_cancel.contextId)
        await updater.update_status(
            TaskState.canceled,
            new_agent_text_message("The earnings call transcript task has been canceled.", task_to_cancel.contextId, task_to_cancel.id),
            final=True
        )
        return task_to_cancel