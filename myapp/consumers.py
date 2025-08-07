import json
from channels.generic.websocket import AsyncWebsocketConsumer

from asgiref.sync import sync_to_async

class VendorNotification(AsyncWebsocketConsumer):
    async def connect(self):
        from rest_framework.authtoken.models import Token
        token = self.scope["query_string"].decode().split("=")[1]
        token_obj = await sync_to_async(Token.objects.select_related("user").get)(key=token)
        user = token_obj.user
        self.scope["user"] = user
        if user.is_authenticated:
            if user.role == 'vendor':
                group_name=f"vendor_{user.id}"
            elif user.is_staff or user.role == 'admin':
                group_name="admin_notifications"
            else:
                group_name=None
            if group_name:
                self.group_name=group_name
                await self.channel_layer.group_add(self.group_name,self.channel_name)
                await self.accept()
            else:
                await self.close()
        else:
            await self.close()
    async def disconnect(self, code):
        if hasattr(self,"group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name,self.channel_name)
    
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'message':event['message']
        }))
        