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
"""
Default views to manage Xero integration.
All views are marked with login_required since there is no way to find out
any user detail from a Xero session, so you must have a valid user already
registered.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse, Resolver404, resolve
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from djxero.models import XeroAuthFlowState

logger = logging.getLogger(__name__)


def _validate_next(path):
    """
    Utility to validate a "next" parameter and move on.
    todo: add xss protections here
    :param path: path fragment (e.g. /home )
    :return: safe path
    """
    try:
        resolve(path)
        return path
    except Resolver404:
        return '/'


class XeroFlowException(Exception):
    pass


@require_GET
@never_cache
@login_required
def xero_auth_accept(request):
    """
    Completes Oauth 1 flow from Xero
    :param request: HttpRequest with parameters
                    oauth_verifier, oauth_token, and org
    :return: HttpResponseRedirect
    """
    try:
        # retrieve the details for this session
        verifier = request.GET.get('oauth_verifier')
        token = request.GET.get('oauth_token')

        if not verifier or not token:
            raise XeroFlowException(request.GET.get('error', "unknown"),
                                    request.GET.get('error_description',
                                                    'unknown'))
        state_obj = get_object_or_404(XeroAuthFlowState, pk=token)
        # complete the flow
        xerouser = state_obj.complete_flow(verifier, request.user)
        # org should be validated, maybe...?
        xerouser.org = request.GET.get('org')
        xerouser.save()
        # find out where user should go next
        next_page = state_obj.next_page
        # we are done, forget this state
        state_obj.delete()
        # send user on its way
        return redirect(_validate_next(next_page))
    except XeroFlowException as xfe:
        logger.exception(xfe)
        return HttpResponseBadRequest()


@require_GET
@never_cache
@login_required
def xero_auth_start(request):
    """
    Start OAuth 1 flow with xero
    :param request: HttpRequest
    :return: HttpResponseRedirect
    """
    # calculate where MS will send user on success
    acceptance_url = request.build_absolute_uri(
        reverse('xero-auth-accept',
                current_app=request.resolver_match.namespace))

    # validate the 'next' parameter, we don't want an open proxy...
    next_page = _validate_next(request.GET.get('next'))
    # save state for later
    xerostate = XeroAuthFlowState.start_flow(acceptance_url, next_page)
    # send user to MS
    return redirect(xerostate.auth_url)


@require_POST
@never_cache
@login_required
def xero_logout(request):
    """
    Completely remove a Xero account linked to the logged-on user
    :param request: HttpRequest
    :return: redirect to next page
    """
    xerouser = request.user.xerouser
    # unlike o365, there is no point in keeping this around, so delete
    xerouser.delete()
    return redirect(_validate_next(request.POST.get('next')))


@require_GET
@login_required
def xero_interstitial(request):
    """ Ask user to link Xero """
    next_page = request.GET.get('next')
    return render(request, 'xero/interstitial.html',
                  context={'next': _validate_next(next_page)})
