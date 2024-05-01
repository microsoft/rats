import unittest
from rats.annotations import FunctionAnnotations, FunctionAnnotationsBuilder, GroupAnnotations

class TestGroupAnnotations(unittest.TestCase):

    def test_group_annotations(self):
        group_annotations = GroupAnnotations(name='test_function', namespace='test_namespace', groups=('group1', 'group2'))
        self.assertEqual(group_annotations.name, 'test_function')
        self.assertEqual(group_annotations.namespace, 'test_namespace')
        self.assertEqual(group_annotations.groups, ('group1', 'group2'))

class TestFunctionAnnotations(unittest.TestCase):

    def test_with_namespace(self):
        group_annotations1 = GroupAnnotations(name='test_function1', namespace='ns1', groups=('group1',))
        group_annotations2 = GroupAnnotations(name='test_function2', namespace='ns2', groups=('group2',))
        function_annotations = FunctionAnnotations(providers=(group_annotations1, group_annotations2))
        filtered_annotations = function_annotations.with_namespace('ns1')
        self.assertEqual(len(filtered_annotations), 1)
        self.assertEqual(filtered_annotations[0].namespace, 'ns1')

    def test_group_in_namespace(self):
        group_annotations1 = GroupAnnotations(name='test_function1', namespace='ns1', groups=('group1',))
        group_annotations2 = GroupAnnotations(name='test_function2', namespace='ns1', groups=('group2',))
        function_annotations = FunctionAnnotations(providers=(group_annotations1, group_annotations2))
        filtered_annotations = function_annotations.group_in_namespace('ns1', 'group1')
        self.assertEqual(len(filtered_annotations), 1)
        self.assertEqual(filtered_annotations[0].groups, ('group1',))

class TestFunctionAnnotationsBuilder(unittest.TestCase):

    def test_add_and_make(self):
        builder = FunctionAnnotationsBuilder()
        builder.add('ns1', 'group1')
        builder.add('ns1', 'group2')
        annotations = builder.make('test_function')
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].name, 'test_function')
        self.assertEqual(annotations[0].namespace, 'ns1')
        self.assertEqual(annotations[0].groups, ('group1', 'group2'))

if __name__ == '__main__':
    unittest.main()
