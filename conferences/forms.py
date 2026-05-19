import re
from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Application, Review, Room, UserProfile


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            css_class = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{css_class} form-check-input".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = f"{css_class} form-select".strip()
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = f"{css_class} form-control".strip()
                widget.attrs.setdefault("rows", 4)
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs["class"] = f"{css_class} form-control".strip()
                widget.attrs["accept"] = "image/*"
            else:
                widget.attrs["class"] = f"{css_class} form-control".strip()
            if field.required:
                widget.attrs["data-required"] = "true"


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(label="Логин")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": "Неверный логин или пароль. Проверьте данные и попробуйте снова.",
        "inactive": "Аккаунт отключен.",
    }


class UserRegisterForm(StyledFormMixin, UserCreationForm):
    """
    Форма регистрации пользователя. 
    Добавляет валидацию логина, телефона и ФИО.
    """
    full_name = forms.CharField(label="ФИО", max_length=180)
    phone = forms.CharField(
        label="Телефон",
        max_length=32,
        widget=forms.TextInput(attrs={"placeholder": "+7 (___) ___-__-__", "data-phone-mask": "true"}),
    )
    email = forms.EmailField(label="Email")

    class Meta:
        model = User
        fields = ["username", "full_name", "phone", "email", "password1", "password2"]
        labels = {
            "username": "Логин",
            "password1": "Пароль",
            "password2": "Повторите пароль",
        }
        help_texts = {"username": "", "password1": "", "password2": ""}

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        # Проверяем минимальную длину логина
        if len(username) < 6:
            raise forms.ValidationError("Логин должен содержать минимум 6 символов.")
        # Логин должен состоять только из латинских букв и цифр
        if not re.fullmatch(r"[A-Za-z0-9]+", username):
            raise forms.ValidationError("Используйте только латинские буквы и цифры.")
        # Проверяем уникальность логина без учета регистра
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Этот логин уже занят.")
        return username

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        # Извлекаем только цифры из введенной строки
        digits = re.sub(r"\D", "", phone)
        # Убеждаемся, что номер телефона состоит из 11 цифр (код + номер)
        if len(digits) != 11:
            raise forms.ValidationError("Введите телефон в формате +7 (999) 999-99-99.")
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get("password1", "")
        if len(password) < 8:
            raise forms.ValidationError("Пароль должен содержать минимум 8 символов.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["full_name"]
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                phone=self.cleaned_data["phone"],
            )
        return user


class ApplicationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ["room", "conference_date", "start_time", "payment_method"]
        widgets = {
            "conference_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "start_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
        }
        labels = {
            "room": "Помещение",
            "conference_date": "Дата начала конференции",
            "start_time": "Предпочтительное время начала",
            "payment_method": "Способ оплаты",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = Room.objects.all()
        self.fields["room"].empty_label = "Выберите помещение"
        self.fields["conference_date"].input_formats = ["%Y-%m-%d"]
        self.fields["start_time"].input_formats = ["%H:%M"]
        self.fields["conference_date"].help_text = "Полный формат даты: ДД.ММ.ГГГГ."
        self.fields["payment_method"].help_text = "Оплата наличными или банковской картой."

    def clean_conference_date(self):
        conference_date = self.cleaned_data["conference_date"]
        if conference_date < date.today():
            raise forms.ValidationError("Дата конференции не может быть в прошлом.")
        return conference_date


class RoomForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "name",
            "room_type",
            "description",
            "image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status"]


class ReviewForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.Select(
                choices=[
                    (5, "5 - отлично"),
                    (4, "4 - хорошо"),
                    (3, "3 - нормально"),
                    (2, "2 - плохо"),
                    (1, "1 - очень плохо"),
                ]
            ),
            "text": forms.Textarea(attrs={"placeholder": "Опишите, насколько удобно прошло мероприятие"}),
        }
        labels = {"rating": "Оценка", "text": "Текст отзыва"}
