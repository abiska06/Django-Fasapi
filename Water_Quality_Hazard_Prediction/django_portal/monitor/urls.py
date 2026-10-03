from django.urls import path

from . import views

app_name = "monitor"

urlpatterns = [
    path("", views.predict_view, name="predict"),
    path("history/", views.history_view, name="history"),
]
