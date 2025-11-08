import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PostsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "posts"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ WebSocket connected: {self.channel_name}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"🔌 WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            
            print(f"📨 Received WebSocket message: {message}")
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'post_update',
                    'message': message
                }
            )
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing WebSocket message: {e}")

    async def post_update(self, event):
        message = event['message']
        post_id = event.get('post_id')
        comment_id = event.get('comment_id')
        liked = event.get('liked')
        like_count = event.get('like_count')
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'post_update',
            'message': message,
            'post_id': post_id,
            'comment_id': comment_id,
            'liked': liked,
            'like_count': like_count
        }))
        print(f"📤 Sent WebSocket update: {message}")