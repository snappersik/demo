from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .forms import (
    ApplicationForm,
    ApplicationStatusForm,
    LoginForm,
    ReviewForm,
    RoomForm,
    UserRegisterForm,
)
from .models import Application, Review, Room


SLIDER_IMAGES = [
    {"src": "img/auditorium3.jpg", "title": "Аудитория для пленарных заседаний"},
    {"src": "img/co-working1.jpg", "title": "Коворкинг для секций и переговоров"},
    {"src": "img/cinema1.jpg", "title": "Кинозал для больших презентаций"},
    {"src": "img/co-working3.jpg", "title": "Деловая площадка с техникой"},
]


def _is_admin(user):
    return user.is_authenticated and user.is_staff


def _status_badge(status):
    return {
        Application.Status.NEW: "badge-new",
        Application.Status.SCHEDULED: "badge-scheduled",
        Application.Status.COMPLETED: "badge-completed",
    }.get(status, "badge-new")


def register_view(request):
    """
    Представление для регистрации новых пользователей.
    Автоматически авторизует пользователя после успешной регистрации.
    """
    if request.user.is_authenticated:
        return redirect("room_list")

    form = UserRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Регистрация прошла успешно. Можно создавать заявку.")
        return redirect("room_list")

    return render(request, "registration/register.html", {"form": form})


class AppLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "registration/login.html"

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse_lazy("admin_dashboard")
        return reverse_lazy("room_list")


class AppLogoutView(LogoutView):
    pass


def room_list(request):
    rooms = Room.objects.all().order_by("room_type", "name")
    return render(
        request,
        "conferences/room_list.html",
        {
            "rooms": rooms,
            "room_types": Room.RoomType.choices,
            "slider_images": SLIDER_IMAGES,
        },
    )


@login_required
def create_application(request):
    if request.user.is_staff:
        messages.info(request, "Администратор управляет заявками через панель администратора.")
        return redirect("admin_dashboard")

    initial = {}
    # Предзаполняем поле помещения, если ID передан через GET или POST запрос
    room_id = request.GET.get("room") or request.POST.get("room")
    if room_id:
        initial["room"] = room_id

    form = ApplicationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.save()
        messages.success(request, "Заявка создана со статусом «новая».")
        return redirect("my_applications")

    return render(request, "conferences/application_form.html", {"form": form, "mode": "create"})


@login_required
def my_applications(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")

    applications = (
        Application.objects.select_related("room", "review")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "conferences/my_applications.html",
        {
            "applications": applications,
            "review_form": ReviewForm(),
            "slider_images": SLIDER_IMAGES,
        },
    )


@login_required
@require_POST
def create_review(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related("room"),
        pk=application_id,
        user=request.user,
    )
    if not application.can_review:
        messages.warning(request, "Отзыв можно оставить только после завершения мероприятия.")
        return redirect("my_applications")

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.application = application
        review.user = request.user
        review.save()
        messages.success(request, "Спасибо, отзыв сохранен.")
    else:
        messages.error(request, "Проверьте оценку и текст отзыва.")

    return redirect("my_applications")


@login_required
@user_passes_test(_is_admin)
def admin_dashboard(request):
    applications = (
        Application.objects.select_related("user", "user__profile", "room", "review")
        .order_by("-created_at")
    )
    return render(
        request,
        "conferences/admin_dashboard.html",
        {
            "rooms": Room.objects.all(),
            "applications": applications,
            "status_choices": Application.Status.choices,
            "room_types": Room.RoomType.choices,
        },
    )

@login_required
@user_passes_test(_is_admin)
def create_room(request):
    form = RoomForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("admin_dashboard")
    return render(request, "conferences/room_form.html", {"form": form, "mode": "create"})


@login_required
@user_passes_test(_is_admin)
@require_POST
def delete_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if room.applications.exists():
        room.is_available = False
        room.save(update_fields=["is_available"])
    else:
        room.delete()
    return redirect("admin_dashboard")


@login_required
@user_passes_test(_is_admin)
@require_POST
def update_application_status(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    form = ApplicationStatusForm(request.POST, instance=application)
    if not form.is_valid():
        return JsonResponse({"ok": False, "error": "Некорректный статус"}, status=400)

    form.save()
    return JsonResponse(
        {
            "ok": True,
            "status": application.status,
            "status_display": application.get_status_display(),
            "badge_class": _status_badge(application.status),
        }
    )
