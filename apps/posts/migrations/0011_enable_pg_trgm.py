from django.db import connection, migrations


def enable_pg_trgm(apps, schema_editor):
    """Only run CREATE EXTENSION on PostgreSQL."""
    if connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


def disable_pg_trgm(apps, schema_editor):
    if connection.vendor == "postgresql":
        schema_editor.execute("DROP EXTENSION IF EXISTS pg_trgm;")


class Migration(migrations.Migration):
    dependencies = [
        ('posts', '0010_post_text_content_alter_post_content'),
    ]

    operations = [
        migrations.RunPython(enable_pg_trgm, disable_pg_trgm),
    ]
