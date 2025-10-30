"""
WebSocket consumers for real-time chat functionality
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
import jwt
from .models import ChatRoom, Message
from datetime import datetime

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        
        # Get token from query string
        token = None
        query_string = self.scope.get('query_string', b'').decode()
        if query_string:
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token')
        
        if not token:
            await self.close()
            return
        
        # Authenticate user
        self.user = await self.get_user_from_token(token)
        if not self.user:
            await self.close()
            return
        
        # Check if user has access to this chat
        has_access = await self.check_chat_access(self.chat_id, self.user)
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user joined notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user.username,
                'user_id': self.user.id
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Send user left notification
            if hasattr(self, 'user'):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'user': self.user.username,
                        'user_id': self.user.id
                    }
                )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                message = text_data_json['message']
                
                # Save message to database
                message_obj = await self.save_message(self.chat_id, self.user, message)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'user': self.user.username,
                        'user_id': self.user.id,
                        'message_id': message_obj.id,
                        'timestamp': message_obj.created_at.isoformat(),
                        'avatar': await self.get_user_avatar(self.user)
                    }
                )
                
            elif message_type == 'file_message':
                message = text_data_json.get('message', 'Sent files')
                files = text_data_json.get('files', [])
                
                # Save message to database (file messages are saved via API, this is just for notification)
                # Send notification to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'user': self.user.username,
                        'user_id': self.user.id,
                        'message_id': None,  # Will be set by API
                        'timestamp': datetime.now().isoformat(),
                        'avatar': await self.get_user_avatar(self.user),
                        'message_type': 'file_message',
                        'files': files
                    }
                )
                
            elif message_type == 'typing':
                # Handle typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user': self.user.username,
                        'user_id': self.user.id,
                        'is_typing': text_data_json.get('is_typing', False)
                    }
                )
                
            elif message_type == 'mark_read':
                # Mark messages as read
                message_id = text_data_json.get('message_id')
                if message_id:
                    await self.mark_message_read(message_id, self.user)
            
            # WebRTC Call Signaling Messages
            elif message_type == 'call_offer':
                recipient_id = text_data_json.get('recipient_id')
                offer = text_data_json.get('offer')
                room_id = text_data_json.get('room_id')
                is_video = text_data_json.get('is_video', False)
                
                # Send call offer to specific user
                await self.send_to_user(recipient_id, {
                    'type': 'call_offer',
                    'offer': offer,
                    'room_id': room_id,
                    'sender_id': self.user.id,
                    'sender_name': self.user.username,
                    'is_video': is_video
                })
                
            elif message_type == 'call_answer':
                recipient_id = text_data_json.get('recipient_id')
                answer = text_data_json.get('answer')
                room_id = text_data_json.get('room_id')
                
                # Send call answer to specific user
                await self.send_to_user(recipient_id, {
                    'type': 'call_answer',
                    'answer': answer,
                    'room_id': room_id,
                    'sender_id': self.user.id
                })
                
            elif message_type == 'ice_candidate':
                recipient_id = text_data_json.get('recipient_id')
                candidate = text_data_json.get('candidate')
                room_id = text_data_json.get('room_id')
                
                # Send ICE candidate to specific user
                await self.send_to_user(recipient_id, {
                    'type': 'ice_candidate',
                    'candidate': candidate,
                    'room_id': room_id,
                    'sender_id': self.user.id
                })
                
            elif message_type == 'call_end':
                recipient_id = text_data_json.get('recipient_id')
                room_id = text_data_json.get('room_id')
                
                # Send call end to specific user
                await self.send_to_user(recipient_id, {
                    'type': 'call_end',
                    'room_id': room_id,
                    'sender_id': self.user.id
                })
                
            elif message_type == 'call_declined':
                recipient_id = text_data_json.get('recipient_id')
                room_id = text_data_json.get('room_id')
                
                # Send call declined to specific user
                await self.send_to_user(recipient_id, {
                    'type': 'call_declined',
                    'room_id': room_id,
                    'sender_id': self.user.id
                })
                
            elif message_type == 'message_deleted':
                message_id = text_data_json.get('message_id')
                chat_id = text_data_json.get('chat_id')
                
                # Send message deletion notification to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id,
                        'chat_id': chat_id,
                        'user_id': self.user.id
                    }
                )
                    
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        user_id = event['user_id']
        message_id = event['message_id']
        timestamp = event['timestamp']
        avatar = event['avatar']
        message_type = event.get('message_type', 'message')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': message_type,
            'message': message,
            'user': user,
            'user_id': user_id,
            'message_id': message_id,
            'timestamp': timestamp,
            'avatar': avatar,
            'files': event.get('files', [])
        }))

    async def typing_indicator(self, event):
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }))

    async def user_joined(self, event):
        # Don't send join notification to the user who joined
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user': event['user'],
                'user_id': event['user_id']
            }))

    async def user_left(self, event):
        # Don't send leave notification to the user who left
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user': event['user'],
                'user_id': event['user_id']
            }))

    async def message_deleted(self, event):
        # Send message deletion notification to all users in the chat
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
            'chat_id': event['chat_id'],
            'user_id': event['user_id']
        }))

    async def send_to_user(self, user_id, message):
        """Send a message to a specific user in the chat room"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_specific_message',
                'message': message,
                'target_user_id': user_id
            }
        )

    async def user_specific_message(self, event):
        """Handle user-specific messages (like call signaling)"""
        if event['target_user_id'] == self.user.id:
            await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            # Decode JWT token
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')
            if user_id:
                return User.objects.get(id=user_id)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            pass
        return None

    @database_sync_to_async
    def check_chat_access(self, chat_id, user):
        try:
            chat_room = ChatRoom.objects.get(id=chat_id)
            return chat_room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, chat_id, user, message_content):
        try:
            chat_room = ChatRoom.objects.get(id=chat_id)
            message = Message.objects.create(
                chat_room=chat_room,
                sender=user,
                content=message_content,
                message_type='text'
            )
            
            # Update chat room's last message
            chat_room.last_message = message_content
            chat_room.last_message_at = message.created_at
            chat_room.last_message_by = user
            chat_room.save()
            
            return message
        except ChatRoom.DoesNotExist:
            raise Exception("Chat room not found")

    @database_sync_to_async
    def mark_message_read(self, message_id, user):
        try:
            message = Message.objects.get(id=message_id)
            message.mark_as_read(user)
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def get_user_avatar(self, user):
        try:
            if hasattr(user, 'profile') and user.profile.avatar:
                return user.profile.avatar.url
        except:
            pass
        return None
