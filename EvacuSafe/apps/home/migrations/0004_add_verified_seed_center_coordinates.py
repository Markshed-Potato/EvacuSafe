from decimal import Decimal

from django.db import migrations


CENTERS = {
    'Cebu City Sports Complex': (Decimal('10.300541'), Decimal('123.895260')),
    'Talamban Elementary School': (Decimal('10.370106'), Decimal('123.917313')),
}


def add_verified_coordinates(apps, schema_editor):
    EvacuationCenter = apps.get_model('home', 'EvacuationCenter')
    for name, (latitude, longitude) in CENTERS.items():
        EvacuationCenter.objects.filter(
            name=name,
            latitude__isnull=True,
            longitude__isnull=True,
        ).update(latitude=latitude, longitude=longitude)


def remove_verified_coordinates(apps, schema_editor):
    EvacuationCenter = apps.get_model('home', 'EvacuationCenter')
    for name, (latitude, longitude) in CENTERS.items():
        EvacuationCenter.objects.filter(
            name=name,
            latitude=latitude,
            longitude=longitude,
        ).update(latitude=None, longitude=None)


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_evacuationcenter_latitude_evacuationcenter_longitude'),
    ]

    operations = [
        migrations.RunPython(add_verified_coordinates, remove_verified_coordinates),
    ]
