from django.contrib import admin

from .models import Memory

@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    readonly_fields=('created','updated',)
    list_display=('id','created','text','category','person',)
    list_display_links = ('id','created',)
    