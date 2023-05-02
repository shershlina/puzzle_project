from django.db import models


class CreatedModel(models.Model):
    """Абстрактная модель с датой создания."""
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        abstract = True
