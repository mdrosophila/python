from django.db import models

# Create your models here.
class Member(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, null=True)
    join_date = models.DateField(null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"