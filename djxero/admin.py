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

from django.contrib import admin

from djxero.models import XeroAuthFlowState, XeroUser, XeroSecret


@admin.register(XeroAuthFlowState)
class XeroAuthFlowAdmin(admin.ModelAdmin):
    date_hierarchy = "created_on"
    list_display = ('oauth_token', 'created_on', 'next_page')


@admin.register(XeroUser)
class XeroUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_on')
    search_fields = ['user__username',
                     'user__last_name', 'user__first_name',
                     'org']


@admin.register(XeroSecret)
class XeroSecretAdmin(admin.ModelAdmin):
    list_display = ('name', 'label')
