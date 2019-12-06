
import sys
import unittest


def run_functional_tests(pattern=None):
    print("Running tests...")
    if pattern is None:
        tests = unittest.defaultTestLoader.discover(".")
    else:
        pattern_with_globs = "%s" % (pattern,)
        tests = unittest.defaultTestLoader.discover(".",
                                                    pattern=pattern_with_globs)
    runner = unittest.TextTestRunner()
    runner.run(tests)


if __name__ == "__main__":
    print("""
    TIP: Use a pattern to specify the test names or nothing for everyone.
    Example: test_imagev*
    """)

    if len(sys.argv) == 1:
        run_functional_tests()
    else:
        run_functional_tests(pattern=sys.argv[1])
