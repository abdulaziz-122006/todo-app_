from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    priority = models.CharField(max_length=20, default="O'rta")
    completed = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)     # Bajarish muddati (vaqti)
    notified = models.BooleanField(default=False)              # Bildirishnoma yuborilganmi
    created_at = models.DateTimeField(auto_now_add=True)       # Yaratilgan vaqti
    completed_at = models.DateTimeField(null=True, blank=True) # Bajarilgan vaqti

    def __str__(self):
        return self.title