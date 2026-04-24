from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .org import Center

User = get_user_model()

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Διαχειριστής'),
        ('staff', 'Συνεργάτης'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    center = models.ForeignKey(Center, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Δομή")
    role = models.CharField("Ρόλος", max_length=10, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    class Meta:
        verbose_name = "Προφίλ Χρήστη"
        verbose_name_plural = "Προφίλ Χρηστών"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()