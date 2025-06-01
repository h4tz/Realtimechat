from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from .models import Message
from asgiref.sync import sync_to_async



User = get_user_model()

def get_private_room_name(user1, user2):
    return f'private_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}'

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return
        self.user = self.scope['user']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
            
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print (f"user {self.user.username}  connected to room {self.room_name} ")
    
    async def disconnect(self, close_code):
        print(f"User {self.user.username} disconnected from room {self.room_name}")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        user = self.scope['user']
        
        if text_data_json.get('typing'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type' : 'typing.indicator', 'user' : self.user.username}
            )
        elif message :
            await sync_to_async(Message.objects.create)(room=self.room_name, user= user, content=message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'chat.message', 'message': message, 'user': user.username}
            )
        else:
            await self.send(text_data=json.dumps({'error': 'Inavalid Payload'}))
    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        await self.send(text_data=json.dumps({'message': message, 'user': user}))
        
    async def chat_typing(self, event):
        user = event['user']
        await self.send(text_data=json.dumps({'typing' : True, 'user': user}))
        
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps(
            {
                'type' : 'typing_indicator',
                'user' : event.get('user', 'unknown'),
                'is_typing': event.get('is_typing', False)
            }
        ))
    async def broadcast_typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing.indicator',
            'user': event['user'],
            'is_typing': event['is_typing'],
    }))

class PrivateChatConsumer(ChatConsumer):
    async def connect(self):
        user1 = self.scope['user']
        user2 = await sync_to_async(User.objects.get)(username=self.scope['url_route']['kwargs']['username'])
        self.room_name = get_private_room_name(user1, user2)
        self.room_group_name = f'chat_{self.room_name}'
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    
