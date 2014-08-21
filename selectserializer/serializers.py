from rest_framework import serializers
from rest_framework.pagination import PaginationSerializer
def _normalize_paths(paths):
    """ select/exclude should be able to take:
            1. a comma-separated string of dotted paths
            2. a list of dotted paths
            3. an already processed nested dictionary
        and return a nested dictionary of excluded/included fields suitable for recursively
        passing to child serializers/fields to properly exclude/include fields.

        this:
        ['a.b.c', 'a.b.d', 'e', 'f.g'] or 'a.b.c,a.b.d,e,f.g'
        becomes:
        {'a': {'b': {'c': {}, 'd': {}}}, 'e': {}, 'f': {'g': {}}}
    """
    if not paths:
        return {}
    # if paths is a dict-like object, skip processing
    if hasattr(paths, 'get'):
        return paths

    try:
        paths = paths.split(',')
    except:
        pass
    paths = (path.split('.') for path in paths)

    out = {}
    for path in paths:
        subdict_pointer = out  # reset out_subdict to the outermost dict
        for segment in path:
            subdict_pointer = subdict_pointer.setdefault(segment, {})
    return out

    """
    A serializer that can be passed a list of dotted fields to select or exclude.
    If instead passed a querydict, will look for `select` and `exclude` keys.

    select and exclude can be a list or a comma-separated string.

    dotted paths let you specify a field nested deep within nested serializers

    if no select or exclude specified all fields are returned.
    """


class SelectFieldMixin(object):
    def initialize(self, parent, field_name):
        super(SelectFieldMixin, self).initialize(parent, field_name)
        parent_select = getattr(parent, 'select', {})
        parent_exclude = getattr(parent, 'exclude', {})
        self.select = parent_select.get(field_name, {})
        self.exclude = parent_exclude.get(field_name, {})

class SelectSerializerMixin(SelectFieldMixin):
    def __init__(self, instance=None, select=None, exclude=None, querydict=None, *args, **kwargs):
        if querydict is not None:
            select = querydict.get('select', {})
            exclude = querydict.get('exclude', {})
        self.select = _normalize_paths(select)
        self.exclude = _normalize_paths(exclude)
        return super(SelectSerializerMixin, self).__init__(instance, *args, **kwargs)

    def to_native(self, obj):
        """
        Serialize objects -> primitives.
        """
        ret = self._dict_class()
        ret.fields = self._dict_class()

        for field_name, field in self.fields.items():
            if (field.read_only and obj is None) or \
               (self.select and field_name not in self.select) or \
               (self.exclude.get(field_name) == {}):
               continue
            field.initialize(parent=self, field_name=field_name)
            key = self.get_field_key(field_name)
            value = field.field_to_native(obj, field_name)
            method = getattr(self, 'transform_%s' % field_name, None)
            if callable(method):
                value = method(obj, value)
            if not getattr(field, 'write_only', False):
                ret[key] = value
            ret.fields[key] = self.augment_field(field, field_name, key, value)

        return ret

class SelectSerializer(SelectSerializerMixin, serializers.Serializer):
    pass

class SelectModelSerializer(SelectSerializerMixin, serializers.Serializer):
    pass

class SelectPaginationSerializer(SelectSerializerMixin, PaginationSerializer):
    pass
