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
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import CASCADE
from encrypted_model_fields.fields import EncryptedTextField
from xero import Xero
from xero.auth import PublicCredentials

logger = logging.getLogger(__name__)

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
    xero_id = models.CharField(max_length=255, blank=True, null=True,
                               help_text="User ID in Xero. "
                                         "Note that this has to be manually "
                                         "retrieved with custom logic, because "
                                         "there is no way to find it from "
                                         "a token; so it's blank by default.")
    xero_email = models.EmailField(max_length=255, blank=True, null=True,
                                   help_text="Email registered with Xero. "
                                             "If present, it overrides "
                                             "User.email when dealing with Xero")
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
        """
        Get a dict with the current token info
        :return: dict
        """
        return json.loads(self.last_token, object_hook=_datetime_parser_hook)

    @property
    def client(self):
        """
        Get a ready-made xero.Xero object
        :return: xero.Xero instance
        """
        return Xero(credentials=PublicCredentials(**self.token),
                    user_agent=get_xero_consumer_key())

    def guess_user_details(self):
        """
        Xero provides no way to find user details from a oauth1.0 token, but
        if we have a prepopulated user we can make an educated guess.
        This is not foolproof, of course, which is why we don't automatically
        set the xero_id field.
        Use at your own risk.
        :return: dict with user details that we *think* might be from the user
                who generated the token, or None if not found anything
        """
        filters = [
            # django_field_name, xero_field_name
            ('email', 'emailaddress'),
            ('first_name', 'firstname'),
            ('last_name', 'lastname')
        ]

        params = {xerokey: getattr(self.user, djkey)
                  for djkey, xerokey in filters}

        if self.xero_email:
            params['emailaddress'] = self.xero_email

        while True:
            result = self.client.users.filter(**params)
            if len(result) > 0:
                return result[0]

            if params.get('emailaddress', None):
                # try again with just the email
                params.pop('firstname')
                params.pop('lastname')
            else:
                break

        return None

    def _request_data(self, verb, url, **kwargs):
        """
        Utility for authenticated calls to Xero apis not yet supported by
        pyxero, getting json back. Note that pagination is NOT handled.

        :param verb: 'get','post',...
        :param url: url to call
        :param kwargs: extra parameters to pass to requests
        :return: list of returned json dicts
        """
        result = self._request(verb, url, **kwargs)
        if result.status_code != 200:
            raise Exception(f"Unexpected response: "
                            f"{result.status_code} {result.text}\n"
                            f"Call was: {verb} {url}\n"
                            f"Args: {kwargs}")
        data = result.json()
        if settings.DEBUG:
            from pprint import pprint
            pprint(data)
        return data

    def _request(self, verb, url, **kwargs):
        """
        Utility for authenticated calls to Xero apis not yet supported by pyxero
        :param verb: 'get','post',...
        :param url: url to call
        :param kwargs: extra parameters to pass to requests
        :return: list of returned json dicts
        """
        creds = self.accounts.credentials
        try:
            result = getattr(
                requests, verb.lower()
            )(url, auth=creds.oauth,
              headers={'User-Agent': creds.consumer_key},
              **kwargs)
            return result
        except Exception as e:
            logger.exception(e)
            return None


class XeroProjectsUser(models.Model):
    """ It turns out that the Projects API has different IDs..."""
    xerouser = models.ForeignKey(XeroUser, on_delete=CASCADE,
                                 related_name='prjuser',
                                 help_text="Regular Xero user ID")
    prj_user_id = models.UUIDField(help_text="Xero user ID in the Projects API")

    BASE_URI = "https://api.xero.com/projects.xro/2.0"

    def guess_projects_user_id(self):
        """
        Xero provides no way to find user details from a oauth1.0 token, but
        if we have a prepopulated user we can make an educated guess.
        This is not foolproof, of course, which is why we don't automatically
        fill it up. Use at your own risk.

        :return: dict with user details that we *think* might be from the user
                who generated the token, or None if not found anything"""
        page = 1
        pagesize = 50
        end_page = 2
        email_lookup = self.xerouser.xero_email or self.xerouser.user.email
        if not email_lookup:
            raise Exception("You cannot guess a Projects user without an email "
                            "set. Add a value to XeroUser.xero_email or "
                            "User.email, and try again.")
        while page <= end_page:
            url = f'{self.BASE_URI}/projectsusers?page={page}&pagesize={pagesize}'
            result = self.xerouser._request_data('get', url)
            for user in result['items']:
                if user['email'] == email_lookup:
                    return user['userId']
            # not found? next page
            end_page = result['pageCount']
            page += 1
        # still here ? Not found
        return None
