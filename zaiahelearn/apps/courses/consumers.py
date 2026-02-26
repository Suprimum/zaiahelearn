import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Classroom, ClassroomMessage, ClassroomMember



class ChatConsumer(AsyncWebsocketConsumer):

    

    live_sessions = {}   # classroom_id -> teacher_id
    video_participants = {}  # classroom_id -> set(usernames)
    
    async def connect(self):
        self.classroom_id = self.scope["url_route"]["kwargs"]["classroom_id"]
        self.room_group_name = f"classroom_{self.classroom_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

        # send history only to this user
        history = await self.get_history()
        await self.send(json.dumps({
            "type": "history",
            "messages": history
        }))

        # broadcast participants update
        users = await self.get_participants()
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "participants_event", "users": users}
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    # ================= RECEIVE =================

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "chat":
            saved = await self.save_message(data["message"])
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_event", "message": saved}
            )

        elif msg_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "typing_event", "user": self.user.username}
            )

        elif msg_type == "start_live":
            if await self.is_teacher():

                # prevent multiple sessions
                if self.classroom_id in self.live_sessions:
                    return

                self.live_sessions[self.classroom_id] = self.user.id
                self.video_participants[self.classroom_id] = set()

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "live_started_event"}
                )


        elif msg_type == "end_live":
            if await self.is_teacher():

                self.live_sessions.pop(self.classroom_id, None)
                self.video_participants.pop(self.classroom_id, None)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "live_ended_event"}
                )


        elif msg_type == "join_video":

            # session must exist
            if self.classroom_id not in self.live_sessions:
                return

            users = self.video_participants[self.classroom_id]

            # prevent duplicate joins
            if self.user.username in users:
                return

            users.add(self.user.username)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "video_join_event",
                    "username": self.user.username
                }
            )


        elif msg_type == "signal":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "signal_event",
                    "from": self.user.username,
                    "signal": data["signal"]
                }
            )

    # ================= GROUP EVENTS =================

    async def chat_event(self, event):
        await self.send(json.dumps({
            "type": "chat",
            "message": event["message"]
        }))

    async def typing_event(self, event):
        await self.send(json.dumps({
            "type": "typing",
            "user": event["user"]
        }))

    async def participants_event(self, event):
        await self.send(json.dumps({
            "type": "participants",
            "users": event["users"]
        }))

    async def live_started_event(self, event):
        await self.send(json.dumps({"type": "live_started"}))

    async def live_ended_event(self, event):
        await self.send(json.dumps({"type": "live_ended"}))

    async def video_join_event(self, event):
        await self.send(json.dumps({
            "type": "video_ready",
            "username": event["username"]
        }))

    async def signal_event(self, event):
        await self.send(json.dumps({
            "type": "signal",
            "from": event["from"],
            "signal": event["signal"]
        }))

    # ================= DATABASE =================

    @database_sync_to_async
    def save_message(self, text):
        classroom = Classroom.objects.get(id=self.classroom_id)

        msg = ClassroomMessage.objects.create(
            classroom_id=classroom.id,
            sender=self.user,
            message=text
        )

        return {
            "username": self.user.username,
            "message": text,
            "is_teacher": self.user == classroom.teacher
        }

    @database_sync_to_async
    def get_history(self):
        classroom = Classroom.objects.get(id=self.classroom_id)
        msgs = ClassroomMessage.objects.filter(
            classroom_id=classroom.id
        ).select_related("sender")[:50]

        return [m.serialize(classroom.teacher) for m in msgs]
    
    @database_sync_to_async
    def start_live_session(self):
        classroom = Classroom.objects.get(id=self.classroom_id)
        if classroom.live_session_active:
            return False

        classroom.live_session_active = True
        classroom.live_session_host = self.user
        classroom.save()
        return True

    @database_sync_to_async
    def end_live_session(self):
        classroom = Classroom.objects.get(id=self.classroom_id)
        classroom.live_session_active = False
        classroom.live_session_host = None
        classroom.save()



    @database_sync_to_async
    def get_participants(self):
        classroom = Classroom.objects.get(id=self.classroom_id)

        students = User.objects.filter(
            id__in=ClassroomMember.objects.filter(
                classroom=classroom,
                approved=True
            ).values_list("student_id", flat=True)
        )

        users = list(students) + [classroom.teacher]
        return [u.username for u in users]

    @database_sync_to_async
    def is_teacher(self):
        classroom = Classroom.objects.get(id=self.classroom_id)
        return self.user == classroom.teacher
