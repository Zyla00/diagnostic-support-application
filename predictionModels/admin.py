from django.contrib import admin
from .models import KnowledgeNote, TrainingJob

@admin.register(KnowledgeNote)
class KnowledgeNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title", "text")

@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = ("model_name", "status", "created_at", "started_at", "finished_at")
    list_filter = ("model_name", "status")
