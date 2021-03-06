import itertools
import unittest

from dndice.lib.evaltree import EvalTreeNode, EvalTree
from dndice.lib.exceptions import EvaluationError, InputTypeError
from dndice.lib.operators import OPERATORS, random, Roll


def trees_equal(a: EvalTree, b: EvalTree) -> bool:
    for nodeA, nodeB in itertools.zip_longest(a.pre_order(), b.pre_order(),
                                              fillvalue=EvalTreeNode(None)):
        if nodeA.payload != nodeB.payload:
            return False
    return True


def tree_empty(tree: EvalTree) -> bool:
    for node in tree.pre_order():
        if node.value is not None:
            return False
    return True


class TreeTester(unittest.TestCase):
    def setUp(self) -> None:
        EvalTree.__eq__ = trees_equal
        i = -1
        rands = [1, 20, 1, 20, 1, 20]

        def mock_randint(start, end):
            nonlocal i
            i += 1
            if i < len(rands):
                return rands[i]
            return 4

        random.randint = mock_randint

    def test_node(self):
        node = EvalTreeNode(4)
        self.assertEqual(node.payload, 4)
        self.assertIs(node.left, None)
        self.assertIs(node.right, None)
        self.assertIs(node.value, None)
        node.evaluate()
        self.assertEqual(node.payload, node.value)

    def test_tree_from_tokens(self):
        fromTokens = EvalTree([4, OPERATORS['d'], 6])
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(6))
        self.assertEqual(fromTokens, expected)

    def test_tree_from_existing(self):
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(6))
        fromExisting = EvalTree(expected)
        self.assertEqual(fromExisting, expected)

    def test_tree_wrong_type(self):
        with self.assertRaises(InputTypeError):
            EvalTree({'invalid'})

    def test_empty_tree_evaluate(self):
        self.assertEqual(EvalTree(None).evaluate(), 0)

    def test_tree_simple_parse(self):
        expr = '4d6'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['d'],
                                     EvalTreeNode(4),
                                     EvalTreeNode(6))
        self.assertEqual(tree, expected)

    def test_tree_basic_precedence(self):
        expr = '2d6 + 5*2^2'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(OPERATORS['d'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(6)),
                                     EvalTreeNode(OPERATORS['*'],
                                                  EvalTreeNode(5),
                                                  EvalTreeNode(OPERATORS['^'],
                                                               EvalTreeNode(2),
                                                               EvalTreeNode(2))))
        self.assertEqual(tree, expected)

    def test_tree_associativity(self):
        expr = '3+4-5'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['-'],
                                     EvalTreeNode(OPERATORS['+'],
                                                  EvalTreeNode(3),
                                                  EvalTreeNode(4)),
                                     EvalTreeNode(5))
        self.assertEqual(tree, expected)
        expr = '3 ^ 2 ^ 4'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['^'],
                                     EvalTreeNode(3),
                                     EvalTreeNode(OPERATORS['^'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(4)))
        self.assertEqual(tree, expected)

    def test_tree_parentheses(self):
        expr = '3+(8-5)'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(3),
                                     EvalTreeNode(OPERATORS['-'],
                                                  EvalTreeNode(8),
                                                  EvalTreeNode(5)))
        self.assertEqual(tree, expected)

    def test_tree_unnecessary_parentheses(self):
        expr = '2*((8)+(4))'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['*'],
                                     EvalTreeNode(2),
                                     EvalTreeNode(OPERATORS['+'],
                                                  EvalTreeNode(8),
                                                  EvalTreeNode(4)))
        self.assertEqual(tree, expected)
        expr = '((3))'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(3)
        self.assertEqual(tree, expected)

    def test_unary_prefix(self):
        expr = '+3'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['p'],
                                     None,
                                     EvalTreeNode(3))
        self.assertEqual(tree, expected)

    def test_unary_suffix(self):
        expr = '4!'
        tree = EvalTree(expr)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['!'],
                                     EvalTreeNode(4))
        self.assertEqual(tree, expected)

    def test_tree_addition(self):
        expr1 = '2d20'
        tree1 = EvalTree(expr1)
        expr2 = '5+3'
        tree2 = EvalTree(expr2)
        tree = tree1 + tree2
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(OPERATORS['d'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(20)),
                                     EvalTreeNode(OPERATORS['+'],
                                                  EvalTreeNode(5),
                                                  EvalTreeNode(3)))
        self.assertEqual(tree, expected)
        tree1copy = EvalTree(None)
        tree1copy.root = EvalTreeNode(OPERATORS['d'],
                                      EvalTreeNode(2),
                                      EvalTreeNode(20))
        # Ensure that the original is untouched
        tree.evaluate()
        self.assertEqual(tree1, tree1copy)
        self.assertTrue(tree_empty(tree1))

    def test_tree_in_place_addition(self):
        expr1 = '2d20'
        tree1 = EvalTree(expr1)
        expr2 = '5+3'
        tree2 = EvalTree(expr2)
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['+'],
                                     EvalTreeNode(OPERATORS['d'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(20)),
                                     EvalTreeNode(OPERATORS['+'],
                                                  EvalTreeNode(5),
                                                  EvalTreeNode(3)))
        # Also test in-place concatenation
        tree1 += tree2
        self.assertEqual(tree1, expected)

    def test_tree_addition_wrong_type(self):
        tree = EvalTree('2d20')
        with self.assertRaises(InputTypeError):
            tree += 1
        with self.assertRaises(InputTypeError):
            tree + 1

    def test_tree_subtraction(self):
        expr1 = '2d20'
        tree1 = EvalTree(expr1)
        expr2 = '5+3'
        tree2 = EvalTree(expr2)
        tree = tree1 - tree2
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['-'],
                                     EvalTreeNode(OPERATORS['d'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(20)),
                                     EvalTreeNode(OPERATORS['+'],
                                                  EvalTreeNode(5),
                                                  EvalTreeNode(3)))
        self.assertEqual(tree, expected)
        tree1copy = EvalTree(None)
        tree1copy.root = EvalTreeNode(OPERATORS['d'],
                                      EvalTreeNode(2),
                                      EvalTreeNode(20))
        # Ensure that the original is untouched
        tree.evaluate()
        self.assertEqual(tree1, tree1copy)
        self.assertTrue(tree_empty(tree1))

    def test_tree_in_place_subtraction(self):
        expr1 = '2d20'
        tree1 = EvalTree(expr1)
        expr2 = '5+3'
        tree2 = EvalTree(expr2)
        # Also test in-place concatenation
        tree1 -= tree2
        expected = EvalTree(None)
        expected.root = EvalTreeNode(OPERATORS['-'],
                                     EvalTreeNode(OPERATORS['d'],
                                                  EvalTreeNode(2),
                                                  EvalTreeNode(20)),
                                     EvalTreeNode(OPERATORS['+'],
                                                  EvalTreeNode(5),
                                                  EvalTreeNode(3)))
        self.assertEqual(tree1, expected)

    def test_tree_subtraction_wrong_type(self):
        expr = '2d20'
        tree = EvalTree(expr)
        with self.assertRaises(InputTypeError):
            tree -= 1
        with self.assertRaises(InputTypeError):
            tree - 1

    def test_eval_failure(self):
        expr = '2d20h(7/2)'
        with self.assertRaises(EvaluationError):
            EvalTree(expr).evaluate()

    def test_critify(self):
        root = EvalTreeNode(OPERATORS['d'],
                            EvalTreeNode(1),
                            EvalTreeNode(OPERATORS['d'],
                                         EvalTreeNode(4),
                                         EvalTreeNode(20)))
        tree = EvalTree(None)
        tree.root = root
        tree.critify()
        self.assertEqual(tree.root.payload, OPERATORS['dc'])
        self.assertEqual(tree.root.right.payload, OPERATORS['dc'])

    def test_maxify(self):
        root = EvalTreeNode(OPERATORS['d'],
                            EvalTreeNode(1),
                            EvalTreeNode(OPERATORS['d'],
                                         EvalTreeNode(4),
                                         EvalTreeNode(20)))
        tree = EvalTree(None)
        tree.root = root
        tree.maxify()
        self.assertEqual(tree.root.payload, OPERATORS['dm'])
        self.assertEqual(tree.root.right.payload, OPERATORS['dm'])

    def test_averageify(self):
        root = EvalTreeNode(OPERATORS['d'],
                            EvalTreeNode(1),
                            EvalTreeNode(OPERATORS['d'],
                                         EvalTreeNode(4),
                                         EvalTreeNode(20)))
        tree = EvalTree(None)
        tree.root = root
        tree.averageify()
        self.assertEqual(tree.root.payload, OPERATORS['da'])
        self.assertEqual(tree.root.right.payload, OPERATORS['da'])

    def test_is_critical(self):
        tree = EvalTree('2d20h1')
        tree.evaluate()
        self.assertTrue(tree.is_critical())
        self.assertFalse(tree.is_fail())
        tree = EvalTree('10d20h5l2')
        tree.evaluate()
        self.assertFalse(tree.is_critical())
        self.assertFalse(tree.is_fail())

    def test_is_fail(self):
        tree = EvalTree('2d20l1')
        tree.evaluate()
        self.assertTrue(tree.is_fail())
        self.assertFalse(tree.is_critical())
        tree = EvalTree('1d20 + 1d20')
        tree.evaluate()
        self.assertTrue(tree.is_fail())
        self.assertTrue(tree.is_critical())

    def test_copy(self):
        root = EvalTreeNode(OPERATORS['d'],
                            EvalTreeNode(1),
                            EvalTreeNode(OPERATORS['d'],
                                         EvalTreeNode(4),
                                         EvalTreeNode(20)))
        tree = EvalTree(None)
        tree.root = root
        tree.evaluate()
        copy = tree.copy()
        self.assertEqual(tree, copy)
        self.assertIsNot(tree, copy)
        for origNode, copyNode in zip(tree.pre_order(), copy.pre_order()):
            self.assertIsNot(origNode, copyNode)
            # Avoid false positives from int interning
            if not isinstance(origNode.value, int):
                self.assertIsNot(origNode.value, copyNode.value)
            if not isinstance(origNode.payload, int):
                self.assertIsNot(origNode.payload, copyNode.payload)

    def test_print_roll(self):
        root = EvalTreeNode(OPERATORS['+'],
                            EvalTreeNode(1),
                            EvalTreeNode(OPERATORS['d'],
                                         EvalTreeNode(4),
                                         EvalTreeNode(20)))
        tree = EvalTree(None)
        tree.root = root
        self.assertEqual(tree.verbose_result(), '1+' + str(Roll([1, 20, 1, 20], 20)) + ' = 43')

    def test_print_empty(self):
        tree = EvalTree(None)
        self.assertEqual(tree.verbose_result(), '')

    def test_print_unary(self):
        root = EvalTreeNode(OPERATORS['m'],
                            None,
                            EvalTreeNode(4))
        tree = EvalTree(None)
        tree.root = root
        self.assertEqual(tree.verbose_result(), '-4 = -4')
        # The other unary operator, !, has a high enough precedence to
        # be evaluated before printing so it isn't shown

    def test_print_parentheses(self):
        root = EvalTreeNode(OPERATORS['*'],
                            EvalTreeNode(2),
                            EvalTreeNode(OPERATORS['+'],
                                         EvalTreeNode(4),
                                         EvalTreeNode(8)))
        tree = EvalTree(None)
        tree.root = root
        self.assertEqual(tree.verbose_result(), '2*(4+8) = 24')

    def test_print_high_precedence(self):
        root = EvalTreeNode(OPERATORS['m'],
                            None,
                            EvalTreeNode(OPERATORS['!'],
                                         EvalTreeNode(5)))
        tree = EvalTree(None)
        tree.root = root
        # it evaluates ! before display because of its high precedence
        self.assertEqual(tree.verbose_result(), '-120 = -120')

    def test_print_unnecessary_parentheses(self):
        tree = EvalTree('1+(2*4)')
        self.assertEqual(tree.verbose_result(), '1+2*4 = 9')

    def test_in_order_roundtrip(self):
        tree = EvalTree('(2)*(4+8)')
        tokens = [node.payload for node in tree.in_order()]
        reconstructed = EvalTree(tokens)
        self.assertEqual(tree, reconstructed)


if __name__ == '__main__':
    unittest.main()
