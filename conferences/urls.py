from django.urls import path

from .views import (
    AppLoginView,
    AppLogoutView,
    admin_dashboard,
    create_application,
    create_review,
    create_room,
    delete_room,
    my_applications,
    register_view,
    room_list,
    update_application_status,
)

urlpatterns = [
    path("", room_list, name="room_list"),
    path("register/", register_view, name="register"),
    path("login/", AppLoginView.as_view(), name="login"),
    path("logout/", AppLogoutView.as_view(), name="logout"),
    path("applications/new/", create_application, name="create_application"),
    path("cabinet/", my_applications, name="my_applications"),
    path("cabinet/review/<int:application_id>/", create_review, name="create_review"),
    path("admin-panel/", admin_dashboard, name="admin_dashboard"),
    path("admin-panel/rooms/new/", create_room, name="create_room"),
    path("admin-panel/rooms/<int:room_id>/delete/", delete_room, name="delete_room"),
    path(
        "admin-panel/applications/<int:application_id>/status/",
        update_application_status,
        name="update_application_status",
    ),
]
