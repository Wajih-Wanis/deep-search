from app.models.message import Message
from app.models.chat import Chat
from Agent.Agent import DeepSearchAgent
from Utils.Model import OllamaModel
import uuid
import jsonify 
from datetime import datetime

def handle_chat(user_id, data):
    # Regular chat handling
    message = data.get('message')
    chat_id = data.get('chat_id')
    
    # Save user message
    user_msg = Message.create(
        chat_id=chat_id,
        content=message,
        role='user'
    )
    
    # Process with AI
    model = OllamaModel()
    response = model._run(message)
    
    # Save AI response
    ai_msg = Message.create(
        chat_id=chat_id,
        content=response,
        role='assistant'
    )
    
    return jsonify({
        'response': response,
        'message_id': str(ai_msg.id)
    })

def handle_deep_search(user_id, data):
    # Initialize search agent
    model = OllamaModel()
    agent = DeepSearchAgent(model=model)
    
    # Create new chat session
    chat = Chat.create(
        user_id=user_id,
        title=f"Deep Search - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        is_deep_search=True
    )
    
    # Run search agent workflow
    workflow = agent.create_graph()
    results = workflow.invoke({"topic": data.get('query')})
    
    # Save results
    Message.create(
        chat_id=str(chat.id),
        content=results['final_response'],
        role='assistant',
        metadata={'type': 'deep_search'}
    )
    
    return jsonify({
        'chat_id': str(chat.id),
        'results': results['final_response']
    })