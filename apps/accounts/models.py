from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import BaseModel
from .managers import UserManager


class User(AbstractUser, BaseModel):
    username = None

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.email})"