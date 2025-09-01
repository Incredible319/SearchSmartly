from django.contrib import admin
from django.db.models import Avg
from .models import PointOfInterest
from django.db import models

@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    """Admin interface for Point of Interest model."""
    
    list_display = [
        'internal_id', 
        'name', 
        'external_id', 
        'category', 
        'average_rating_display',
        # 'latitude',
        # 'longitude'
    ]
    
    list_filter = ['category', 'created_at', 'updated_at']
    
    search_fields = ['internal_id', 'external_id', 'name', 'category', 'description']
    
    readonly_fields = ['internal_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('internal_id', 'external_id', 'name', 'category')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Details', {
            'fields': ('ratings', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def average_rating_display(self, obj):
        """Display average rating with 2 decimal places."""
        try:
            return f"{obj.average_rating:.2f}"
        except:
            return "0.00"
    average_rating_display.short_description = 'Avg. Rating'
    
    def has_add_permission(self, request):
        """Disable manual addition - PoIs should only be imported via command."""
        return False
