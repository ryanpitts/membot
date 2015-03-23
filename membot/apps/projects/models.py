from datetime import datetime, timedelta

from django.db import models
from django.template.defaultfilters import date as dj_date

class Project(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'projects'
        ordering = ('-created',)
    
    def __unicode__(self):
        return '{0}'.format(self.name)
        
    def next_itemdate(self):
        today = datetime.today().date()
        try:
            return self.projectdate_set.filter(itemdate__gte=today)[0]
        except:
            return ''

class ProjectBulletPoint(models.Model):
    project = models.ForeignKey(Project)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    description = models.TextField('Text')

    class Meta:
        ordering = ('-created',)
    
    def __unicode__(self):
        return '{0}: {1}'.format(self.project.name, self.pk)

class ProjectDate(models.Model):
    project = models.ForeignKey(Project)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    itemdate = models.DateField()
    itemtime = models.TimeField(blank=True, null=True)

    class Meta:
        ordering = ('itemdate', 'itemtime')
    
    def __unicode__(self):
        return '{0}: {1}'.format(self.project.name, self.name)
        
    def naturaldate(self):
        today = datetime.today().date()
        if self.itemdate == today:
            return 'Today'
        if self.itemdate == (today + timedelta(days=1)):
            return 'Tomorrow'
        if self.itemdate < (today + timedelta(days=6)):
            return dj_date(self.itemdate, "l")
        return dj_date(self.itemdate, "F d")
        
    def within_week(self):
        today = datetime.today().date()
        return self.itemdate < (today + timedelta(days=6))
        
class ProjectLink(models.Model):
    project = models.ForeignKey(Project)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    url = models.URLField()

    class Meta:
        ordering = ('-created',)
    
    def __unicode__(self):
        return '{0}: {1}'.format(self.project.name, self.name)

