from django.urls import path

from europilot.api import health, investigation_detail, investigation_list


urlpatterns = [
    path("api/health/", health),
    path("api/v1/investigations/", investigation_list),
    path("api/v1/investigations/<str:investigation_id>/", investigation_detail),
]
