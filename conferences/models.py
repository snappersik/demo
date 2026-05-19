from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
# from django.urls import reverse


class UserProfile(models.Model):
    """
    Профиль пользователя для хранения дополнительных данных: ФИО, телефон и роль.
    Связан один-к-одному со стандартной моделью User(Django).
    """
    class Role(models.TextChoices):
        USER = "user", "Пользователь"
        ADMIN = "admin", "Администратор"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    full_name = models.CharField("ФИО", max_length=180)
    phone = models.CharField("Телефон", max_length=32)
    role = models.CharField("Роль", max_length=12, choices=Role.choices, default=Role.USER)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.full_name or self.user.username


class Room(models.Model):
    class RoomType(models.TextChoices):
        AUDITORIUM = "auditorium", "Аудитория"
        COWORKING = "coworking", "Коворкинг"
        CINEMA = "cinema", "Кинозал"

    name = models.CharField("Название", max_length=160)
    room_type = models.CharField("Тип помещения", max_length=20, choices=RoomType.choices)
    description = models.TextField("Описание")
    image = models.ImageField("Изображение", upload_to="rooms/")

    class Meta:
        verbose_name = "Помещение"
        verbose_name_plural = "Помещения"
        ordering = ["room_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"


class Application(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        SCHEDULED = "scheduled", "Мероприятие назначено"
        COMPLETED = "completed", "Мероприятие завершено"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "оплата в офисе организации"
        CARD = "card", "оплата картой МИР"
        QRCODE = "qrcode", "предоплата по QR-коду"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conference_applications",
        verbose_name="Пользователь",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name="Помещение",
    )
    conference_date = models.DateField("Дата конференции")
    start_time = models.TimeField("Время начала")
    payment_method = models.CharField("Способ оплаты", max_length=12, choices=PaymentMethod.choices)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "conference_date"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"Заявка #{self.pk}: {self.room.name} на {self.conference_date:%d.%m.%Y}"

    @property
    def can_review(self):
        return self.status == self.Status.COMPLETED and not hasattr(self, "review")

    @property
    def can_user_change(self):
        return self.status == self.Status.NEW


class Review(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name="Заявка",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Пользователь",
    )
    rating = models.PositiveSmallIntegerField(
        "Оценка",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField("Отзыв")
    created_at = models.DateTimeField("Дата отзыва", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating}/5 от {self.user.username}"
