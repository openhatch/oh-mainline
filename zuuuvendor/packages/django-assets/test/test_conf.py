from django_assets import conf as assets_conf
from django import conf as django_conf


def test_read():
    """Test that we can read Django's own config values from our
    own settings object.
    """
    django_conf.settings.TOP_SECRET = 1234
    assert assets_conf.settings.TOP_SECRET == 1234

    # Test a again, to make sure that the settings object didn't
    # just copy the data once on initialization.
    django_conf.settings.TOP_SECRET = 'helloworld'
    assert assets_conf.settings.TOP_SECRET == 'helloworld'


def test_write():
    """Test that changing a value to our configuration also updates
    the original Django settings object.
    """
    assert not getattr(django_conf.settings, 'FOOBAR', None) == 1234
    assets_conf.settings.FOOBAR = 1234
    assert django_conf.settings.FOOBAR == 1234