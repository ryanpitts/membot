from django.db import models

class Memory(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    text = models.TextField(blank=True)
    category = models.CharField(max_length=64, blank=True)
    person = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'membot'
        ordering = ('-created',)
        verbose_name_plural = 'Memories'
    
    def __unicode__(self):
        return '%s %s %s' % (self.category, self.created, self.person)
    