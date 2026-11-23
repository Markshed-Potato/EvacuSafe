from django.db import migrations


LEGACY_COLUMN_DEFAULTS = {
    'home_evacuationcenter': {
        'current_occupancy': '0',
        'max_capacity': '0',
        'operational_status': "'Active'",
    },
    'profile_profile': {
        'avatar_color': "''",
        'display_name': "''",
        'updated_at': 'CURRENT_TIMESTAMP',
    },
    'user_settings_usersettings': {
        'compact_dashboard': 'FALSE',
        'reduced_motion': 'FALSE',
        'show_timestamps': 'TRUE',
    },
}


def set_legacy_column_defaults(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'postgresql':
        return

    with connection.cursor() as cursor:
        for table, defaults in LEGACY_COLUMN_DEFAULTS.items():
            cursor.execute(
                """
                SELECT column_name, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                """,
                [table],
            )
            columns = dict(cursor.fetchall())
            for column, default in defaults.items():
                if column in columns and columns[column] is None:
                    cursor.execute(
                        'ALTER TABLE {} ALTER COLUMN {} SET DEFAULT {}'.format(
                            schema_editor.quote_name(table),
                            schema_editor.quote_name(column),
                            default,
                        )
                    )


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0006_evacuationcenter_archived_at_and_more'),
        ('profile', '0002_alter_profile_role'),
        ('user_settings', '0002_alter_usersettings_dark_mode'),
    ]

    operations = [
        migrations.RunPython(
            set_legacy_column_defaults,
            migrations.RunPython.noop,
        ),
    ]
