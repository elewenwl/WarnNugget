class PreferenceKeyReset(bytes):
    """In-process reset request, resolved against a backup before delivery."""

    def __new__(cls, paths):
        paths = tuple(sorted(set(tuple(path) for path in paths)))
        if not paths or any(not path or any(not isinstance(key, str) or not key
                                           for key in path) for path in paths):
            raise ValueError('Preference reset requires explicit key paths.')
        instance = super().__new__(cls, b'')
        instance.paths = paths
        return instance
