from django.db import models


class PointOfInterest(models.Model):
    """Point of Interest model to store data from CSV, JSON, and XML files."""
    
    # Internal ID (auto-generated primary key)
    internal_id = models.AutoField(primary_key=True)
    
    # External ID from different file formats
    external_id = models.CharField(max_length=100, unique=True, help_text="External ID from the source file")
    
    # Name field
    name = models.CharField(max_length=255, help_text="Name of the Point of Interest")
    
    # Location coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=8, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, help_text="Longitude coordinate")
    
    # Category
    category = models.CharField(max_length=100, help_text="Category of the Point of Interest")
    
    # Ratings (stored as JSON to handle multiple ratings)
    ratings = models.JSONField(default=list, help_text="List of ratings for this PoI")
    
    # Additional fields
    description = models.TextField(blank=True, null=True, help_text="Description of the Point of Interest")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Point of Interest"
        verbose_name_plural = "Points of Interest"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.external_id})"
    
    @property
    def average_rating(self):
        """Calculate the average rating from the ratings list."""
        try:
            if not self.ratings:
                return 0.0
            # Ensure ratings is a list
            if isinstance(self.ratings, (int, float)):
                return float(self.ratings)
            if isinstance(self.ratings, list):
                return sum(self.ratings) / len(self.ratings)
            return 0.0
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0
