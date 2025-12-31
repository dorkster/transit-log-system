from django.db import migrations

def update_posttrip_checklist(apps, schema_editor):
    PreTrip = apps.get_model('transit', 'PreTrip')
    for pt in PreTrip.objects.all():
        if pt.inspect_type != 1:
            continue
        
        # if pre-trip flags are all good, then set the post-trip flags as good
        if pt.cl_fluids == 2 and pt.cl_engine == 2 and pt.cl_headlights == 2 and pt.cl_hazards == 2 and pt.cl_directional == 2 and pt.cl_markers == 2 and pt.cl_windshield == 2 and pt.cl_glass == 2 and pt.cl_mirrors == 2 and pt.cl_doors == 2 and pt.cl_tires == 2 and pt.cl_leaks == 2 and pt.cl_body == 2 and pt.cl_registration == 2 and pt.cl_wheelchair == 2 and pt.cl_mechanical == 2 and pt.cl_interior == 2:
            pt.cl_post_interior = 2
            pt.cl_post_exterior = 2
            pt.cl_post_issues = 2
            pt.save()

class Migration(migrations.Migration):
    dependencies = [
        ('transit', '0124_pretrip_cl_post_exterior_pretrip_cl_post_interior_and_more'),
    ]

    operations = [
        migrations.RunPython(update_posttrip_checklist),
    ]

