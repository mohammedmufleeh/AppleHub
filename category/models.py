from distutils.command.upload import upload
from django.db import models

# Create your models here.

class category(models.Model):
    category_name = models.CharField(max_length=50,unique=True)
    slug = models.SlugField(max_length=100,unique=True)
    description = models.TextField(max_length=255,blank=True)
    cat_image = models.ImageField(upload_to='photo/category', blank=True)\

    class Meta:
     verbose_name_plural = 'category'


    def __str__(self):
        return self.category_name