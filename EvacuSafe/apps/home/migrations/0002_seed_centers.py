from django.db import migrations


def seed_centers(apps, schema_editor):
    EvacuationCenter = apps.get_model('home', 'EvacuationCenter')
    centers = [
        dict(name="Barangay San Isidro Gymnasium", location="San Isidro, Cebu City", capacity=300, occupants=210, status='active'),
        dict(name="Cebu City Sports Complex", location="Cebu City", capacity=800, occupants=612, status='active'),
        dict(name="Talamban Elementary School", location="Talamban, Cebu City", capacity=250, occupants=0, status='standby'),
        dict(name="Mabolo Covered Court", location="Mabolo, Cebu City", capacity=150, occupants=98, status='active'),
        dict(name="Lahug Multipurpose Hall", location="Lahug, Cebu City", capacity=200, occupants=0, status='closed'),
    ]
    for c in centers:
        EvacuationCenter.objects.get_or_create(name=c['name'], defaults=c)


def unseed_centers(apps, schema_editor):
    EvacuationCenter = apps.get_model('home', 'EvacuationCenter')
    EvacuationCenter.objects.filter(name__in=[
        "Barangay San Isidro Gymnasium",
        "Cebu City Sports Complex",
        "Talamban Elementary School",
        "Mabolo Covered Court",
        "Lahug Multipurpose Hall",
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_centers, unseed_centers),
    ]
