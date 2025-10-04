from django.db import models



class Comment(models.Model):
    text = models.TextField("Comentario")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario {self.id} - {self.created_at:%Y-%m-%d %H:%M}"
