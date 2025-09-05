from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/consultation/(?P<consultation_id>\w+)/$', consumers.ConsultationConsumer.as_asgi()),
]
