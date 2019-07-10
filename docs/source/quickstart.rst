=======
Quickstart
=======

There is a ``@xero_required`` decorator for views, which will automatically
check if an active Xero session is present. If not, it will redirect to an interstitial page
asking the user to do the authentication dance. You can control that page by creating a
custom template ``xero/interstitial.html`` (make sure it has a link to ``xero-auth-start`` somewhere).

Once authorized, in your view you will get a `.xerouser` attribute which you can use to do stuff like:
::
   from djxero.decorators import xero_required

   @login_required
   @xero_required
   def my_view(request):
       client = request.user.xerouser.client
       contacts = client.contacts.all()
       ...

That client is a preconfigured ``xero.Xero`` object from `pyxero <https://github.com/freakboy3742/pyxero>`_.

Whenever you want to manually trigger authentication with Xero, just redirect to the view
``xero-auth-start`` and this package will do the rest.
The view accepts an optional ``next`` parameter to control where the user will land
on successful authentication; otherwise it will redirect to ``/``.

Xero sessions last for 30 minutes, but if you want to end them earlier, POST to
the view ``xero-logout`` (again with an optional ``next``).

Some details will be exposed in ``User`` instances under ``.xerouser``, but Xero mechanisms
are such that it's all pretty meaningless - there is currently no way to know anything about the user
from the Xero session alone. For that reason, note that **you must have some other registration mechanism to
create a regular Django user first** (e.g. regular login page with some other auth system); this package only extends
that ``User`` instance to attach a temporary Xero session.