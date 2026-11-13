from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Game(models.Model):
    """Model reprezentujący grę komputerową w katalogu."""

    STATUS_RELEASED = 'released'
    STATUS_EARLY_ACCESS = 'early_access'
    STATUS_UPCOMING = 'upcoming'
    STATUS_CHOICES = [
        (STATUS_RELEASED, 'Wydana'),
        (STATUS_EARLY_ACCESS, 'Wczesny dostęp'),
        (STATUS_UPCOMING, 'Zapowiedziana'),
    ]

    title = models.CharField(max_length=100, verbose_name='Tytuł')
    genre = models.CharField(max_length=50, verbose_name='Gatunek')
    release_year = models.IntegerField(verbose_name='Rok wydania')
    description = models.TextField(verbose_name='Opis')
    is_multiplayer = models.BooleanField(default=False, verbose_name='Tryb multiplayer')
    platform = models.CharField(max_length=50, default='PC', verbose_name='Platforma')
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Ocena (0-10)',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RELEASED,
        verbose_name='Status',
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Data dodania')

    class Meta:
        db_table = 'games_game'
        ordering = ['-release_year', 'title']
        verbose_name = 'Gra'
        verbose_name_plural = 'Gry'

    def __str__(self):
        return f"{self.title} ({self.release_year}) [{self.platform}]"

    def to_dict(self):
        """Zwraca słownikową reprezentację gry na potrzeby API JSON."""
        return {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'release_year': self.release_year,
            'description': self.description,
            'is_multiplayer': self.is_multiplayer,
            'platform': self.platform,
            'rating': float(self.rating) if self.rating is not None else None,
            'status': self.status,
            'status_display': self.get_status_display(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
