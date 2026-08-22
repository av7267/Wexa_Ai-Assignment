from django.urls import path

from detector import views


urlpatterns = [
    path("health", views.health, name="health"),
    path("detections/cycles", views.cycles, name="cycles"),
    path("detections/fanout", views.fanout, name="fanout"),
]
