from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    display_name = None

    @property
    def full_label(self):
        return self.get_full_name() or self.username
