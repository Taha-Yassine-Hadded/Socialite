from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_userprofile_email_verification_sent_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='password_reset_code',
            field=models.CharField(blank=True, help_text='Code de réinitialisation de mot de passe (6 chiffres)', max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='password_reset_expires_at',
            field=models.DateTimeField(blank=True, help_text='Expiration du code de réinitialisation', null=True),
        ),
    ]


