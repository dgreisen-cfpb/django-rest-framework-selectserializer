import unittest
from core.serializers import SelectSerializer, SelectModelSerializer
from core.select_serializers import _normalize_paths
from rest_framework import serializers
from django.contrib.auth.models import Group
from django.http import QueryDict
from django.contrib.auth import get_user_model
User = get_user_model()


class SelectSerializerTest(unittest.TestCase):
    def setUp(self):
        class TestObj(object):
            child = lambda x: self.TestObj()
            first = 1
            second = 2
            third = 3

        class TestChildSelectSerializer(SelectSerializer):
            first = serializers.Field(source='first')
            second = serializers.Field(source='second')
            third = serializers.Field(source='third')

        class TestSelectSerializer(SelectSerializer):
            """
            SelectSerializer for testing
            """
            first = serializers.Field(source='first')
            second = serializers.Field(source='second')
            third = serializers.Field(source='third')
            child = TestChildSelectSerializer(source='child')

        self.TestObj = TestObj
        self.TestChildSelectSerializer = TestChildSelectSerializer
        self.TestSelectSerializer = TestSelectSerializer

# _normalize_paths
    def test_normalize_paths_when_passed_dict_expect_dict_returned_unchanged(self):
        cut = _normalize_paths
        param = {'a': {}, 'b': {'c': {}}}

        actual = cut({'a': {}, 'b': {'c': {}}})

        self.assertEqual(actual, param)
    def test_normalize_paths_when_passed_select_list_expect_select_list_stored_on_obj(self):
        cut = _normalize_paths

        actual = cut(['a', 'b'])

        self.assertEqual(actual, {'a': {}, 'b': {}})

    def test_normalize_paths_when_passed_exclude_list_expect_exclude_list_stored_on_obj(self):
        cut = _normalize_paths

        actual = cut(['a', 'b'])

        self.assertEqual(actual, {'a': {}, 'b': {}})

    def test_normalize_paths_when_passed_select_string_expect_select_list_stored_on_obj(self):
        cut = _normalize_paths

        actual = cut('a,b')

        self.assertEqual(actual, {'a': {}, 'b': {}})

    def test_normalize_paths_when_passed_exclude_string_expect_exclude_list_stored_on_obj(self):
        cut = _normalize_paths

        actual = cut('a,b')

        self.assertEqual(actual, {'a': {}, 'b': {}})

    def test_normalize_paths_when_passed_dotted_path_expect_split_on_dots(self):
        cut = _normalize_paths

        actual = cut('a.b,c.d,a.f.g,e')

        self.assertEqual(actual, {'a':{'b': {}, 'f': {'g':{}}}, 'c': {'d': {}}, 'e': {}})

#SelectSerializer.init
    def test_init_when_passed_select_and_exclude_strings_expect_lists_stored_on_obj(self):
        cut = self.TestSelectSerializer

        actual = cut(select=['a', 'b'], exclude=['c', 'd'])

        self.assertEqual(actual.select, {'a': {}, 'b': {}})
        self.assertEqual(actual.exclude, {'c': {}, 'd': {}})

    def test_init_when_passed_querydict_expect_select_exclude_set(self):
        cut = self.TestSelectSerializer

        actual = cut(querydict=QueryDict('select=a,b&exclude=c,d'))

        self.assertEqual(actual.select, {'a': {}, 'b': {}})
        self.assertEqual(actual.exclude, {'c': {}, 'd': {}})

    def test_init_when_passed_querydict_with_no_select_exclude_expect_full_obj(self):
        cut = self.TestSelectSerializer

        actual = cut(querydict=QueryDict('random=string'))

        self.assertEqual(actual.select, {})
        self.assertEqual(actual.exclude, {})

# SelectSerializer.to_native
    def test_to_native_when_no_select_or_exclude_expect_all_fields(self):
        cut = self.TestSelectSerializer(self.TestObj())

        actual = cut.to_native(self.TestObj())

        self.assertEqual(actual, {'first': 1, 'second': 2, 'third': 3, 'child': {'first': 1, 'second': 2, 'third': 3}})

    def test_to_native_when_select_second_field_expect_only_second_field_serialized(self):
        cut = self.TestSelectSerializer(self.TestObj(), select=['second'])

        actual = cut.to_native(self.TestObj())

        self.assertEqual(actual, {'second': 2})

    def test_field_after_data_called_with_select_second_expect_all_fields_present(self):
        cut = self.TestSelectSerializer(self.TestObj(), select=['second'])
        cut.to_native(self.TestObj())

        actual = cut.fields

        self.assertIn('third', actual)

    def test_to_native_when_exclude_second_field_expect_only_first_third_serialized(self):
        cut = self.TestSelectSerializer(self.TestObj(), exclude=['second', 'child'])

        actual = cut.to_native(self.TestObj())

        self.assertEqual(actual, {'first': 1, 'third': 3})

    def test_to_native_when_select_subfield_expect_only_subfield(self):
        cut = self.TestSelectSerializer(self.TestObj(), select=['child.first', 'child.second'])

        actual = cut.to_native(self.TestObj())

        self.assertEqual(actual, {'child': {'first': 1, 'second': 2}})

    def test_to_native_when_exclude_subfield_expect_all_except_subfield(self):
        cut = self.TestSelectSerializer(self.TestObj(), exclude=['child.first', 'child.second'])

        actual = cut.to_native(self.TestObj())

        self.assertEqual(actual, {'first': 1, 'second': 2, 'third': 3, 'child': {'third': 3}})


class SelectModelSerializerTest(unittest.TestCase):
    def setUp(self):

        class GroupSerializer(SelectModelSerializer):
            """
            SelectModelSerializer for testing
            """
            field1 = serializers.SerializerMethodField('_field1')

            def _field1(self, obj):
                return 5

            class Meta:
                model = Group
                fields = ['name', 'field1']

        class UserSerializer(SelectModelSerializer):
            """
            SelectModelSerializer for testing
            """
            groups = GroupSerializer(many=True, source='groups')
            class Meta:
                model = User
                fields = ['first_name', 'last_name', 'username', 'groups']

        self.GroupSerializer = GroupSerializer
        self.UserSerializer = UserSerializer

        self.user, created = User.objects.get_or_create(id=1, defaults={'username': 'ssmith', 'first_name': 'Sally', 'last_name': 'Smith'})
        self.group, created = Group.objects.get_or_create(name='admin')
        self.user.groups.clear()
        self.user.groups.add(self.group)

    # all unit tests for SelectSerializer should apply here b/c we are calling the exact
    # same methods. So just do some sanity checks
    def test_init_when_passed_querydict_expect_select_exclude_set(self):
        cut = self.UserSerializer

        actual = cut(querydict=QueryDict('select=a,b&exclude=c,d.e,d.f.g'))

        self.assertEqual(actual.select, {'a': {}, 'b': {}})
        self.assertEqual(actual.exclude, {'c': {}, 'd': {'e': {}, 'f': {'g': {}}}})

    def test_to_native_when_no_select_exclude_expect_all_fields(self):
        cut = self.UserSerializer(self.user)

        actual = cut.to_native(self.user)

        self.assertEqual(actual, {'first_name': u'system', 'last_name': u'system', 'username': u'system', 'groups': [{'name': u'admin', 'field1': 5}], '_links': {'self': u'/api/users/system/'}})

    def test_to_native_when_select_subfield_expect_only_subfield(self):
        cut = self.UserSerializer(self.user, select=['groups.name', 'username'])

        actual = cut.to_native(self.user)

        self.assertEqual(actual, {'username': self.user.username, 'groups': [{'name': 'admin',}]})

    def test_to_native_when_exclude_subfield_expect_all_except_subfield(self):
        cut = self.UserSerializer(self.user, exclude=['groups.field1', 'first_name', 'last_name'])

        actual = cut.to_native(self.user)

        self.assertEqual(actual, {'username': u'system', 'groups': [{'name': u'admin'}], '_links': {'self': u'/api/users/system/'}})

    def test_include_links_field_when_passed_no_instance_expect_links_field(self):
        cut = self.UserSerializer()
        actual = cut._include_links_field(None)

        self.assertTrue(actual)

