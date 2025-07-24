# test_client.py

import requests
import json
import time
import uuid

# The URL of your running A2A agent server
A2A_AGENT_URL = "http://127.0.0.1:8080"

def start_chat_session():
    """
    Starts an interactive command-line chat session with the agent.
    """
    print("=====================================================")
    print("  Earnings Call Transcript Agent - Interactive Chat  ")
    print("=====================================================")
    print("Type your query and press Enter. Type 'quit' or 'exit' to end.")
    
    session_id = f"chat_session_{uuid.uuid4().hex[:8]}"
    print(f"(Session ID: {session_id})\n")

    while True:
        try:
            query = input("You: ")

            if query.lower() in ["quit", "exit", "bye"]:
                print("\nAgent: Goodbye!\n")
                break
            
            if not query:
                continue

            # This is the corrected payload structure, matching the A2A specification precisely.
            payload = {
                "jsonrpc": "2.0",
                "method": "message/send",  # Correct method name with '/'
                "params": {
                    "message": {
                        "messageId": f"msg_{uuid.uuid4().hex[:8]}", # Correct key is 'messageId'
                        "role": "user",  # Required role field
                        "parts": [{"text": query}],
                        "contextId": session_id,
                    }
                },
                "id": f"req_{uuid.uuid4().hex[:8]}"
            }

            final_response = ""
            print("Agent: Thinking...", end='\r')

            with requests.post(A2A_AGENT_URL, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            event = json.loads(line.decode('utf-8'))
                            
                            # Check for 'working' status and print the thought process
                            if event.get("status") == "working" and event.get("content"):
                                thought = event["content"]["parts"][0]["text"]
                                # Overwrite "Thinking..." with the actual thought
                                print(f"Agent: {thought}...", end='\r')

                            # Check for the final 'completed' status
                            if event.get("status") == "completed" and event.get("content"):
                                final_response = event["content"]["parts"][0]["text"]
                        except json.JSONDecodeError:
                            continue
            
            # Clear the last "Thinking..." or thought line
            print(" " * 80, end='\r')

            if final_response:
                print(f"Agent: {final_response}\n")
            else:
                print("Agent: I'm sorry, I didn't get a final response. Please check the server logs.\n")


        except requests.exceptions.RequestException as e:
            print(f"\n[ERROR] Could not connect to the agent: {e}")
            print("Please ensure all three servers are running.\n")
        except KeyboardInterrupt:
            print("\n\nAgent: Goodbye!\n")
            break
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred: {e}\n")


if __name__ == "__main__":
    start_chat_session()