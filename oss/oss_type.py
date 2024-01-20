from django.db import models


class OssType(models.IntegerChoices):
    MINIO = 1, 'minio'
    OBS = 2, 'obs'
    COS = 3, 'cos'
    ALIBABA = 4, 'alibaba'
