from django.db import migrations, models
import django.db.models.deletion
import utilities.fields


def console_connections_to_cables(apps, schema_editor):
    """
    Copy all existing console connections as Cables
    """
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ConsolePort = apps.get_model('dcim', 'ConsolePort')
    ConsoleServerPort = apps.get_model('dcim', 'ConsoleServerPort')
    Cable = apps.get_model('dcim', 'Cable')

    # Load content types
    consoleport_type = ContentType.objects.get_for_model(ConsolePort)
    consoleserverport_type = ContentType.objects.get_for_model(ConsoleServerPort)

    # Create a new Cable instance from each console connection
    for consoleport in ConsolePort.objects.filter(connected_endpoint__isnull=False):
        c = Cable()
        # We have to assign GFK fields manually because we're inside a migration.
        c.endpoint_a_type = consoleport_type
        c.endpoint_a_id = consoleport.id
        c.endpoint_b_type = consoleserverport_type
        c.endpoint_b_id = consoleport.connected_endpoint_id
        c.connection_status = consoleport.connection_status
        c.save()


def power_connections_to_cables(apps, schema_editor):
    """
    Copy all existing power connections as Cables
    """
    ContentType = apps.get_model('contenttypes', 'ContentType')
    PowerPort = apps.get_model('dcim', 'PowerPort')
    PowerOutlet = apps.get_model('dcim', 'PowerOutlet')
    Cable = apps.get_model('dcim', 'Cable')

    # Load content types
    powerport_type = ContentType.objects.get_for_model(PowerPort)
    poweroutlet_type = ContentType.objects.get_for_model(PowerOutlet)

    # Create a new Cable instance from each power connection
    for powerport in PowerPort.objects.filter(power_outlet__isnull=False):
        c = Cable()
        # We have to assign GFK fields manually because we're inside a migration.
        c.endpoint_a_type = powerport_type
        c.endpoint_a_id = powerport.id
        c.endpoint_b_type = poweroutlet_type
        c.endpoint_b_id = powerport.power_outlet_id
        c.connection_status = powerport.connection_status
        c.save()


def interface_connections_to_cables(apps, schema_editor):
    """
    Copy all InterfaceConnections as Cables
    """
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Interface = apps.get_model('dcim', 'Interface')
    InterfaceConnection = apps.get_model('dcim', 'InterfaceConnection')
    Cable = apps.get_model('dcim', 'Cable')

    # Load content types
    interface_type = ContentType.objects.get_for_model(Interface)

    # Create a new Cable instance from each InterfaceConnection
    for conn in InterfaceConnection.objects.all():
        c = Cable()
        # We have to assign GFK fields manually because we're inside a migration.
        c.endpoint_a_type = interface_type
        c.endpoint_a_id = conn.interface_a_id
        c.endpoint_b_type = interface_type
        c.endpoint_b_id = conn.interface_b_id
        c.connection_status = conn.connection_status
        c.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('dcim', '0065_patch_panel_ports'),
    ]

    operations = [

        # Create the Cable model
        migrations.CreateModel(
            name='Cable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('endpoint_a_id', models.PositiveIntegerField()),
                ('endpoint_b_id', models.PositiveIntegerField()),
                ('type', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('status', models.BooleanField(default=True)),
                ('label', models.CharField(blank=True, max_length=100)),
                ('color', utilities.fields.ColorField(blank=True, max_length=6)),
                ('endpoint_a_type', models.ForeignKey(limit_choices_to={'model__in': ['consoleport', 'consoleserverport', 'interface', 'poweroutlet', 'powerport', 'frontpanelport', 'rearpanelport']}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='contenttypes.ContentType')),
                ('endpoint_b_type', models.ForeignKey(limit_choices_to={'model__in': ['consoleport', 'consoleserverport', 'interface', 'poweroutlet', 'powerport', 'frontpanelport', 'rearpanelport']}, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='cable',
            unique_together={('endpoint_b_type', 'endpoint_b_id'), ('endpoint_a_type', 'endpoint_a_id')},
        ),

        # Rename model fields
        migrations.RenameField(
            model_name='consoleport',
            old_name='cs_port',
            new_name='connected_endpoint'
        ),
        migrations.AlterField(
            model_name='consoleport',
            name='connected_endpoint',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='connected_endpoint', to='dcim.ConsoleServerPort'),
        ),
        migrations.AlterField(
            model_name='consoleserverport',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consoleserverports', to='dcim.Device'),
        ),

        # Copy console/power/interface connections as Cables
        migrations.RunPython(console_connections_to_cables),
        migrations.RunPython(power_connections_to_cables),
        migrations.RunPython(interface_connections_to_cables),

    ]
