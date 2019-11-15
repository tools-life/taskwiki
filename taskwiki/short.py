import six

class ShortUUID(object):
    def __init__(self, value, tw):
        # Extract the UUID from the given object. Support both
        # strings and ShortUUID instances.
        if isinstance(value, six.string_types):
            # Use str reprentation of the value, first 8 chars
            self.value = str(value)[:8]
        elif type(value) is ShortUUID:
            self.value = value.value
        else:
            raise ValueError("Incorrect type for ShortUUID: {0}"
                             .format(type(value)))

        self.tw = tw

    def __eq__(self, other):
        # For full UUIDs, our value is shorter
        # For short, the lengths are the same
        if not isinstance(other, ShortUUID):
            return False

        return other.value == self.value and self.tw == other.tw

    def __hash__(self):
        return self.value.__hash__() * 17 + self.tw.__hash__() * 7

    def __str__(self):
        return self.value

    def vim_representation(self, cache):
        """
        Return 'H:<uuid>' for TW with indicator 'H',
        '<uuid>' for default instance.
        """

        # Determine the key of the TW instance
        [key] = [key for key, value in cache.warriors.items()
                 if value == self.tw]
        prefix = '{0}:'.format(key) if key != 'default' else ''

        # Return the H:<uuid> or <uuid> value
        return '{0}{1}'.format(prefix, self.value)
