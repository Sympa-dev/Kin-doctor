from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import json

class ConsultationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'
        self.user = self.scope['user']

        # Vérifier les permissions
        if not await self.has_consultation_access():
            await self.close()
            return

        # Rejoindre le groupe de la salle
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Notifier les autres participants de la connexion
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'user': self.user.get_full_name(),
                'role': 'doctor' if hasattr(self.user, 'doctor_profile') else 'patient',
                'timestamp': timezone.now().isoformat()
            }
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Notifier les autres participants de la déconnexion
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat()
                }
            )

            # Quitter le groupe de la salle
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')

        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'video_signal':
            await self.handle_video_signal(data)
        elif message_type == 'status_update':
            await self.handle_status_update(data)

    async def handle_chat_message(self, data):
        message = data['message']
        # Sauvegarder le message dans la base de données
        await self.save_chat_message(message)

        # Envoyer le message à tous les participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.get_full_name(),
                'role': 'doctor' if hasattr(self.user, 'doctor_profile') else 'patient',
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_video_signal(self, data):
        # Transmettre les signaux WebRTC
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_signal',
                'signal': data['signal'],
                'from_user': self.user.get_full_name()
            }
        )

    async def handle_status_update(self, data):
        # Gérer les mises à jour de statut (caméra/micro on/off)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_update',
                'status': data['status'],
                'user': self.user.get_full_name()
            }
        )

    async def chat_message(self, event):
        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user': event['user'],
            'role': event['role'],
            'timestamp': event['timestamp']
        }))

    async def video_signal(self, event):
        # Transmettre les signaux WebRTC
        await self.send(text_data=json.dumps({
            'type': 'video_signal',
            'signal': event['signal'],
            'from_user': event['from_user']
        }))

    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': event['status'],
            'user': event['user']
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'user': event['user'],
            'role': event['role'],
            'timestamp': event['timestamp']
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'user': event['user'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def has_consultation_access(self):
        from .models import Consultation
        consultation = Consultation.objects.filter(id=self.consultation_id).first()
        if not consultation:
            return False
        
        if hasattr(self.user, 'doctor_profile'):
            return consultation.doctor.user == self.user
        return consultation.patient.user == self.user

    @database_sync_to_async
    def save_chat_message(self, message):
        from .models import ConsultationMessage
        ConsultationMessage.objects.create(
            consultation_id=self.consultation_id,
            sender=self.user,
            message=message
        )
