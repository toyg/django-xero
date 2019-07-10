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

from django.db import migrations

_DEFAULT_SECRETS = [('xero_consumer_key', 'Consumer Key'),
                    ('xero_consumer_secret', 'Consumer Secret')]


def load_defaults(apps, schema_editor):
    XeroSecret = apps.get_model('djxero', 'XeroSecret')
    db_alias = schema_editor.connection.alias
    defaults = [XeroSecret(name=name, label=label, value='')
                for name, label in _DEFAULT_SECRETS]
    XeroSecret.objects.using(db_alias).bulk_create(defaults)


def purge_defaults(apps, schema_editor):
    XeroSecret = apps.get_model('djxero', 'XeroSecret')
    db_alias = schema_editor.connection.alias
    XeroSecret.objects.using(db_alias).filter(
        name__in=[key for key, label in _DEFAULT_SECRETS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('djxero', '0001_xero_initial')
    ]

    operations = [
        migrations.RunPython(load_defaults, purge_defaults, elidable=True),
    ]
