from channels.generic.websocket import AsyncJsonWebsocketConsumer


class CaseStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.case_id = self.scope["url_route"]["kwargs"]["case_id"]
        self.group_name = f"case_{self.case_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def case_status(self, event):
        await self.send_json(event["payload"])
