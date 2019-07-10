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

import json
from datetime import datetime

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import CASCADE
from encrypted_model_fields.fields import EncryptedTextField
from xero.auth import PublicCredentials

DATETIME_FIELDS = ['oauth_expires_at', 'oauth_authorization_expires_at']


def _datetime_parser_hook(adict):
    """ Utility for json deserialization of naive datetimes. """
    for field in DATETIME_FIELDS:
        if field in adict:
            adict[field] = datetime.strptime(adict[field] + '000',
                                             "%Y-%m-%dT%H:%M:%S.%f")
    return adict


# todo: make secret-handling more flexible
def get_secret(param):
    try:
        secret = XeroSecret.objects.get(name=param)
        return secret.value
    except XeroSecret.DoesNotExist:
        return None


def get_xero_consumer_key():
    return get_secret('xero_consumer_key')


def get_xero_consumer_secret():
    return get_secret('xero_consumer_secret')


# 2019-07-10T11:26:05.125
class XeroSecret(models.Model):
    """
    Configuration data that has to be protected.
    """
    name = models.CharField(max_length=255, primary_key=True,
                            help_text="Key to refer to this secret")
    value = EncryptedTextField(blank=True, default='',
                               help_text="Value to store "
                                         "(will be encrypted in database)")
    label = models.CharField(max_length=255, blank=True, null=True,
                             help_text='Human-readable label or description')

    def __str__(self):
        return self.name


class XeroAuthFlowState(models.Model):
    """ Temporary storage for details of in-flow auth requests.
    Likely to be replaced with redis or something later on."""
    oauth_token = models.TextField(primary_key=True,
                                   help_text="OAuth token to which "
                                             "this request belongs")
    state = EncryptedTextField(help_text="JSON with all values to "
                                         "recreate a  given "
                                         "PublicCredentials state")
    auth_url = models.URLField(null=False, blank=False,
                               max_length=4096,
                               help_text="URL where the user was sent to "
                                         "authenticate")
    next_page = models.CharField(max_length=255,
                                 null=True,
                                 blank=False,
                                 help_text="Where to redirect once successful")

    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.created_on.isoformat() + ' ' + \
               json.loads(self.state)['oauth_token']

    @classmethod
    def start_flow(cls, acceptance_url, next_page=None):
        """
        Start authorization flow
        """
        # instantiating credentials automatically starts the flow
        creds = PublicCredentials(get_xero_consumer_key(),
                                  get_xero_consumer_secret(),
                                  acceptance_url)
        # save state for later
        af_state = cls(state=json.dumps(creds.state,
                                        cls=DjangoJSONEncoder),
                       oauth_token=creds.oauth_token,
                       next_page=next_page)
        af_state.auth_url = creds.url
        af_state.save()
        return af_state

    def complete_flow(self, verification_code, user):
        """ Complete Authorization flow
        Note that you must already have a Django user, since Xero won't tell you
        anything about the logged-on user.

        :param verification_code: code to verify the original request
        :param user: User instance
        :returns XeroUser instance
        """
        # rebuild our connection
        state_dict = json.loads(self.state, object_hook=_datetime_parser_hook)
        creds = PublicCredentials(**state_dict)
        creds.verify(verification_code)
        xero_user = XeroUser.from_state(creds, user)
        return xero_user


class XeroUser(models.Model):
    """ Xero account linked to a User """
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=CASCADE,
                                null=False, blank=False,
                                help_text="Django user")
    org = models.CharField(max_length=255,
                           blank=True, null=True,
                           help_text="Identifier for the org the user belongs "
                                     "to, in theory")
    last_token = EncryptedTextField(blank=True, default='',
                                    help_text="JSON with last successful login "
                                              "details (so you can check if "
                                              "still logged on). ")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @classmethod
    def from_state(cls, creds: PublicCredentials, user):
        """ given a token reference, retrieve or construct a XeroUser instance.
        Note that you must already have a Django user, since Xero won't tell you
        anything about the logged-on user.
        :param creds: PublicCredentials instance with a valid session
        :param user: User instance
        :returns: XeroUser instance
        """
        if not creds.verified:
            raise Exception("Trying to create a XeroUser with "
                            "an invalid session")

        xero_user, created = cls.objects.get_or_create(
            user=user
        )
        xero_user.last_token = json.dumps(creds.state, cls=DjangoJSONEncoder)
        xero_user.save()
        return xero_user

    @property
    def token(self):
        return json.loads(self.last_token, object_hook=_datetime_parser_hook)
