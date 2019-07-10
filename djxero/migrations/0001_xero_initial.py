#  Copyright (c) 2019 Giacomo Lacava <giac@autoepm.com>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='XeroSecret',
            fields=[
                ('name', models.CharField(help_text='Key to refer to this secret', max_length=255, primary_key=True, serialize=False)),
                ('value', encrypted_model_fields.fields.EncryptedTextField(blank=True, default='', help_text='Value to store (will be encrypted in database)')),
                ('label', models.CharField(blank=True, help_text='Human-readable label or description', max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='XeroUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_token', encrypted_model_fields.fields.EncryptedTextField(blank=True, default='', help_text='JSON with last successful login details (so you can check if still logged on). ')),
                ('org', models.CharField(blank=True, help_text='Identifier for the org the user belongs to, in theory', max_length=255, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(help_text='Django user', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='XeroAuthFlowState',
            fields=[
                ('oauth_token', models.TextField(help_text='OAuth token to which this request belongs', primary_key=True, serialize=False)),
                ('state', encrypted_model_fields.fields.EncryptedTextField(help_text='JSON with all values to recreate a  given PublicCredentials state')),
                ('next_page', models.CharField(help_text='Where to redirect once successful', max_length=255, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('auth_url', models.URLField(help_text='URL where the user was sent to authenticate', max_length=4096)),
            ],
        ),
    ]
