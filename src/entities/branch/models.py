import uuid
from django.db import models


class Branch(models.Model):
    """
    Equivalente ao:

        model Branch {
          id         String   @id @default(uuid())
          name       String
          industryId String
          createdAt  DateTime @default(now())
          updatedAt  DateTime @updatedAt
        }

    no schema.prisma.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    industry_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "branches"  # nome da tabela no Postgres
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
