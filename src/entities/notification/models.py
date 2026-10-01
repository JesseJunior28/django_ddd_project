from django.db import models


class Notification(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']
