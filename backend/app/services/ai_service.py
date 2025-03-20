from flask import jsonify
from app.models.message import Message
from app.models.chat import Chat
from app.models.user import User
from Agent.Agent import DeepSearchAgent
from Utils.Model import OllamaModel
from datetime import datetime
import logging

def handle_chat(user_id, data):
    """Handle regular chat interactions"""
    message = data.get('message')
    chat_id = data.get('chat_id')
    
    if not message or not chat_id:
        return jsonify({
            'success': False,
            'error': 'Message and chat_id are required'
        }), 400
    
    try:
        user_msg = Message.create(
            chat_id=chat_id,
            content=message,
            role='user'
        )
        
        user = User.find_by_id(user_id)
        provider = user.get('providers', {}).get('default', 'ollama')
        model_config = user.get('config', {})
        
        try:
            model = OllamaModel._get_model(provider, model_config)
            response = model._run(message)
        except Exception as e:
            logging.error(f"Model error: {str(e)}")
            model = OllamaModel()
            response = model._run(message)
        
        ai_msg = Message.create(
            chat_id=chat_id,
            content=response,
            role='assistant'
        )
        
        return jsonify({
            'success': True,
            'response': response,
            'message_id': str(ai_msg['_id']),
            'created_at': ai_msg['created_at'].isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in handle_chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred processing your request'
        }), 500

def handle_deep_search(user_id, data):
    """Handle deep search requests"""
    query = data.get('query')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query is required'
        }), 400
    
    try:
        user = User.find_by_id(user_id)
        model_config = user.get('config', {})
        
        model_name = model_config.get('model', 'llama3.2:1b')
        model_params = model_config.get('parameters', {})
        temperature = model_params.get('temperature', 0)

        try:
            model = OllamaModel(
                model=model_name,
                temperature=temperature
            )
        except Exception as e:
            logging.error(f"Model initialization failed: {str(e)}, using default")
            model = OllamaModel() 
        agent = DeepSearchAgent(model=model)
        
        chat = Chat.create(
            user_id=user_id,
            title=f"Deep Search: {query[:30]}{'...' if len(query) > 30 else ''}",
            is_deep_search=True
        )
        
        Message.create(
            chat_id=str(chat['_id']),
            content=query,
            role='user'
        )
        
        workflow = agent.create_graph()
        results = workflow.invoke({"topic": query})
        
        ai_msg = Message.create(
            chat_id=str(chat['_id']),
            content=results['final_response'],
            role='assistant',
            metadata={
                'type': 'deep_search',
                'sources': results['final_response'].get('sources', [])
            }
        )
        
        return jsonify({
            'success': True,
            'chat_id': str(chat['_id']),
            'results': results['final_response']
        })
        
    except Exception as e:
        logging.error(f"Error in handle_deep_search: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred processing your deep search request'
        }), 500