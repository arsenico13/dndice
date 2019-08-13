import unittest

from lib import evaltree, exceptions


class TreeTester(unittest.TestCase):
    def test_node(self):
        node = evaltree.EvalTreeNode(4)
        self.assertEqual(node.payload, 4)
        self.assertIs(node.left, None)
        self.assertIs(node.right, None)
        self.assertIs(node.value, None)
        node.evaluate()
        self.assertEqual(node.payload, node.value)

    def test_tree_parse(self):
        pass


if __name__ == '__main__':
    unittest.main()
