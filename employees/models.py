from django.db import models


class Message(models.Model):
    message_id = models.BigAutoField(primary_key=True)  # Use MySQL's 'message_id' as the primary key
    id_chat = models.BigIntegerField(null=True, blank=True)  # Optional for non-Telegram inputs
    platform = models.CharField(max_length=50, null=True, blank=True)  # Matches MySQL's DEFAULT NULL
    lang = models.CharField(max_length=10, null=True, blank=True)  # Matches MySQL's DEFAULT NULL
    message = models.TextField(null=True, blank=True)  # Matches MySQL's DEFAULT NULL
    created_at = models.DateTimeField(auto_now_add=True)  # DEFAULT current_timestamp()

    class Meta:
        db_table = "messages"  # Explicitly match the MySQL table name
