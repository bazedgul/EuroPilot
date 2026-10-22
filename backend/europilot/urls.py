from django.urls import path

from europilot.api import case_detail, case_list, case_note_create, case_transition, health, investigation_detail, investigation_list


urlpatterns = [
    path("api/health/", health),
    path("api/v1/investigations/", investigation_list),
    path("api/v1/investigations/<str:investigation_id>/", investigation_detail),
    path("api/v1/cases/", case_list),
    path("api/v1/cases/<str:case_id>/", case_detail),
    path("api/v1/cases/<str:case_id>/transitions/", case_transition),
    path("api/v1/cases/<str:case_id>/notes/", case_note_create),
]
