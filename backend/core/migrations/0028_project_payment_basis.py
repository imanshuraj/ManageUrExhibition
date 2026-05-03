from django.db import migrations

def drop_payment_basis_if_exists(apps, schema_editor):
    from django.db import connection
    with connection.cursor() as cursor:
        if connection.vendor == 'postgresql':
            cursor.execute("ALTER TABLE core_project DROP COLUMN IF EXISTS payment_basis;")
        elif connection.vendor == 'sqlite':
            # SQLite doesn't support DROP COLUMN IF EXISTS in a simple way 
            # and doesn't support DROP COLUMN at all in older versions.
            # But we can try a simple DROP COLUMN and catch the error.
            try:
                cursor.execute("ALTER TABLE core_project DROP COLUMN payment_basis;")
            except Exception:
                pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_alter_message_content_alter_message_file_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_payment_basis_if_exists),
    ]
