# strings/models.py
import hashlib
import json
from django.db import models
from django.utils import timezone


class AnalyzedString(models.Model):
    """
    Model representing an analyzed string and its computed properties.
    """

    id = models.CharField(
        max_length=64, primary_key=True, editable=False  # SHA256 hash length
    )
    value = models.TextField(unique=True)  # The string itself
    length = models.PositiveIntegerField()
    is_palindrome = models.BooleanField()
    unique_characters = models.PositiveIntegerField()
    word_count = models.PositiveIntegerField()
    sha256_hash = models.CharField(max_length=64)
    character_frequency_map = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Generate hash if not already set
        if not self.id:
            self.sha256_hash = hashlib.sha256(self.value.encode()).hexdigest()
            self.id = self.sha256_hash

        # Auto-compute properties before saving
        self.length = len(self.value)
        cleaned_value = self.value.lower().replace(" ", "")
        self.is_palindrome = cleaned_value == cleaned_value[::-1]
        self.unique_characters = len(set(self.value))
        self.word_count = len(self.value.split())

        # Frequency map
        freq_map = {}
        for char in self.value:
            freq_map[char] = freq_map.get(char, 0) + 1
        self.character_frequency_map = freq_map

        super().save(*args, **kwargs)

    def __str__(self):
        return self.value
