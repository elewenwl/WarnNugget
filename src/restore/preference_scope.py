"""Preference baselines shared by upload capture, pruning and injection."""

DAEMON_OVERRIDE_PATH = 'com.apple.xpc.launchd/disabled.plist'


def is_preference_file(domain, path):
    path = path.lstrip('/')
    return ((domain == 'HomeDomain' and path.startswith('Library/Preferences/') and path.endswith('.plist'))
            or (domain == 'ManagedPreferencesDomain' and path.endswith('.plist'))
            or (domain == 'SystemPreferencesDomain' and path == 'FeatureFlags/Global.plist')
            or (domain == 'DatabaseDomain' and path == DAEMON_OVERRIDE_PATH))


def is_preference_parent(domain, path):
    return path in {
        'HomeDomain': ('', 'Library', 'Library/Preferences'),
        'ManagedPreferencesDomain': ('', 'mobile', 'root'),
        'SystemPreferencesDomain': ('', 'FeatureFlags'),
        'DatabaseDomain': ('', 'com.apple.xpc.launchd'),
    }.get(domain, ())


def is_preference_upload(tree):
    for domain in ('HomeDomain', 'ManagedPreferencesDomain', 'SystemPreferencesDomain', 'DatabaseDomain'):
        prefix = domain + '/'
        if tree.startswith(prefix):
            return is_preference_file(domain, tree[len(prefix):])
    for prefix, domain, relative_prefix in (
        ('Library/Preferences/', 'HomeDomain', 'Library/Preferences/'),
        ('Managed Preferences/', 'ManagedPreferencesDomain', ''),
        ('preferences/', 'SystemPreferencesDomain', ''),
        ('db/', 'DatabaseDomain', ''),
    ):
        if tree.startswith(prefix):
            return is_preference_file(domain, relative_prefix + tree[len(prefix):])
    return False
