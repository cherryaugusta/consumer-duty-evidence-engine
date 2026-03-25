from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("artifacts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS documentsection_embedding_idx ON artifacts_documentsection USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);",
            "DROP INDEX IF EXISTS documentsection_embedding_idx;",
        )
    ]
