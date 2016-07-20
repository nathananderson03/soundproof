
def initialise_django():
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "soundproof.settings")
    import django
    django.setup()
