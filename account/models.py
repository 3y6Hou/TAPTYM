from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.crypto import get_random_string
from .tasks import send_activation_code
from django.core.mail import send_mail


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password, **kwargs):
        assert email, "Email is required"
        email = self.normalize_email(email)
        user:User = self.model(email=email, **kwargs)
        user.set_password(password)
        user.create_activation_code()
        user.save(using=self._db)
        send_activation_code.delay(user.email, user.activation_code)
        return user

    def create_superuser(self, email, password, **kwargs):
        assert email, 'Email is required'
        kwargs['is_active'] = True
        kwargs['is_superuser'] = True
        kwargs['is_staff'] = True
        email = self.normalize_email(email)
        user:User = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = None
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='users', null=True)
    is_active = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=8, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()
    def __str__(self):
        return self.email

    def create_activation_code(self):
        self.activation_code = get_random_string(8, 'qwertyuiopasdfghjklzxcvbnm123456789')

    @staticmethod
    def generate_activation_code():
        from django.utils.crypto import get_random_string
        code = get_random_string(8)
        return code 

    def set_activation_code(self):
        code = self.generate_activation_code()
        if User.objects.filter(activation_code=code).exists():
            self.set_activation_code()
        else:
            self.activation_code = code
            self.save()

    def password_confirm(self):
        activation_url = f'http://34.123.240.158/account/password_confirm/{self.activation_code}'
        message = f"""
        Do you want to change password?
        Confirm password changes: {activation_url}
        """
        send_mail("Please confirm", message, "ruslan883888@gmail.com", [self.email])

    def __str__(self) -> str:
        return f'{self.username} -> {self.email}'