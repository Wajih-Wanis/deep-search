from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from backend.app.models.message import Message

class ChatAgent:
    def __init__(self, chat_id,db):
        self.chat_id = chat_id
        self.checkpointer = MongoDBSaver(
            database=db.db.name,
            collection="chats",
            client=db.db.client
        )
        self.graph = self._build_graph()

    def _build_graph(self):
        # Define state schema
        class AgentState:
            messages: list = []

        # Build workflow
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("process_message", self.process_message)
        workflow.add_node("generate_response", self.generate_response)

        # Connect nodes
        workflow.add_edge("process_message", "generate_response")
        workflow.add_edge("generate_response", END)

        # Configure checkpointing
        workflow.set_entry_point("process_message")
        return workflow.compile(
            checkpointer=self.checkpointer,
            checkpoint_id=str(self.chat_id)
        )

    async def process_message(self, state: dict):
        # Load existing messages from DB
        messages = Message.get_chat_messages(self.chat_id)
        state.messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        return state

    async def generate_response(self, state: dict):
        # Generate response using chat history (replace with actual LLM call)
        last_message = state.messages[-1]["content"] if state.messages else "Hello!"
        response = f"Echo: {last_message}"
        
        # Update state
        state.messages.append({"role": "assistant", "content": response})
        return state

    async def handle_message(self, user_message: str):
        # Run the graph with the new message
        async for event in self.graph.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"configurable": {"thread_id": str(self.chat_id)}}
        ):
            if "messages" in event:
                # Save final state messages to database
                for msg in event["messages"]:
                    if msg["role"] == "user" and msg["content"] == user_message:
                        Message.create(self.chat_id, msg["content"], "user")
                    elif msg["role"] == "assistant":
                        Message.create(self.chat_id, msg["content"], "assistant")
        return event["messages"]