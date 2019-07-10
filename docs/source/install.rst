Installation
------------
1. Install the package
::
   pip install django-xero

2. Add ``encrypted_model_fields`` and ``djxero`` to ``INSTALLED_APPS`` in your settings.
Note that the authentication system is required.
::
   INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.sessions',
        ...
        'encrypted_model_fields',
        'djxero',
        ...
   ]

3. Generate an encryption key:
::
    python -c 'import base64; import os; print(base64.urlsafe_b64encode(os.urandom(32)))'

and add it to your settings. NOTE: in production, you want to store this value very carefully.
::
    FIELD_ENCRYPTION_KEY = b'A7c4T1Kx3XmttUjm2cX8ScYcUEdF7RzFziEzfoBO7x4='

4. Run migrations to create the necessary objects
::
    python manage.py migrate djxero

5. Set the Xero secrets for your public app. You can do this from the admin site (easier),
or directly via ``manage.py shell`` like this:
::
    from djxero.models import XeroSecret
    consumer_key = XeroSecret.objects.get(pk='xero_consumer_key')
    consumer_key.value = 'your key'
    consumer_key.save()
    consumer_secret = XeroSecret.objects.get(pk='xero_consumer_secret')
    consumer_secret.value = 'your secret'
    consumer_secret.save()

6. in your project ``urls.py``, add the following:
::
    urlpatterns = [
       path('xero/', include('djxero.urls')),
       ...
    ]

Optional: in your ``templates`` folder, create a ``xero/interstitial.html`` template to manage the page
that will be shown whenever a user is required to log on Xero.