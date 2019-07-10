# Django-Xero
[Xero](https://xero.com) integration for Django.

## Features
This package allows users to authenticate to Xero via a Public App that you have 
registered on the [Xero Developer Portal](https://developer.xero.com).

Whenever you want to trigger authentication with Xero, just redirect to the view 
`xero-auth-start` and this package will do the rest. 
The view also accepts an optional `next`parameter to control where the user will land 
on successful authentication; otherwise it will redirect to `/`.

Xero sessions last for 30 minutes, but if you want to end them earlier, POST to 
the view `xero-logout` (again with an optional `next`).

There is also a `@xero_required` decorator for views, which will automatically 
check if an active Xero session is present. If not, it will redirect to an interstitial page
asking the user to do the authentication dance. You can control that page by creating a 
custom template `xero/interstitial.html`.

Some details will be exposed in `User` instances under `.xerouser`, but the Xero mechanisms
are such that it's all pretty meaningless. For the same reasons, note that 
***you must have some other registration mechanism to create an 
authenticated user first*** (e.g. regular login page or anything else); this package only extends 
that `User` instance to attach a temporary Xero session.

## Supported Platforms
* Python 3.7 (should work on 3.5/3.6 too, but is untested).
* Django 2

## Requirements
django-xero should automatically download all necessary prerequisites, but I like
to give credit where credit is due. 
We stand on the shoulders of the following giants:

* [django-encrypted-model-fields](https://gitlab.com/lansharkconsulting/django/django-encrypted-model-fields/)
* [pyxero](https://github.com/freakboy3742/pyxero)

## Installation
1. Install the package
    ```
    pip install django-xero
    ```
2. Add `encrypted_model_fields` and `djxero` to `INSTALLED_APPS` in your settings. 
    Note that the authentication system is required.
    ```python
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.sessions',
        ...
        'encrypted_model_fields',
        'djxero',
        ...
    ]
    ```
3. Generate an encryption key:
    ```bash
    python -c 'import base64; import os; print(base64.urlsafe_b64encode(os.urandom(32)))'
    ```
    and add it to your settings. NOTE: in production, you want to store this safely.
    ```python
    FIELD_ENCRYPTION_KEY = b'A7c4T1Kx3XmttUjm2cX8ScYcUEdF7RzFziEzfoBO7x4='
    ```
4. Run migrations to create the necessary objects
    ```bash
    python manage.py migrate djxero
    ```
5. Set the Xero secrets for your public app. You can do this from the admin site (easier),
    or directly via `manage.py shell`:
    ```python
    from djxero.models import XeroSecret
    consumer_key = XeroSecret.objects.get(pk='xero_consumer_key')
    consumer_key.value = 'your key'
    consumer_key.save()
    consumer_secret = XeroSecret.objects.get(pk='xero_consumer_secret')
    consumer_secret.value = 'your secret'
    consumer_secret.save()
    ```
6. in your project `urls.py`, add the following:
    ```python
    urlpatterns = [
       path('xero/', include('djxero.urls')),
       ...
    ]
    ```
    
 ## Issues
 For problems, file an issue on [GitHub](https://github.com/toyg/django-xero).
 The author is available for hire (hint hint).
 
 ## Credits and License
 Copyright (c) 2019 [Giacomo Lacava](https://linkedin.com/in/glacava).
 
 Released under the terms of the Apache Software License, version 2.