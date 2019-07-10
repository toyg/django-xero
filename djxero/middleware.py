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

from datetime import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse


class XeroMiddleware:
    """ Middleware to require a valid Xero session """

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Require a valid Xero session.
        On failure, redirect to view xero-interstitial.
        """
        valid_auth = False
        try:
            xero_user = request.user.xerouser
            # note that all this is not TZ-aware, so all servers have to be on
            # same TZ
            if xero_user.token['oauth_expires_at'] >= datetime.now():
                valid_auth = True
        except (get_user_model().xerouser.RelatedObjectDoesNotExist,
                AttributeError) as e:
            pass
        if not valid_auth:
            return redirect(
                '{url}?next={path}'.format(url=reverse('xero-interstitial'),
                                           path=request.path))
        return None
