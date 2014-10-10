import unittest


class Expectation(object):

  def __init__(self, actual_value, report_error):
    self.actual_value = actual_value
    self.report_error = report_error
    self.want_ok = True
    self.is_complete = False

  def Not(self):
    assert not self.is_complete
    self.want_ok = not self.want_ok
    return self

  def ToSatisfy(self, predicate, description=None):
    if description is None:
      description = 'to satisfy %r' % predicate
    self._End(predicate, description)

  def ToMatch(self, pattern):
    if self.want_ok:
      match = re.match(pattern, self.actual_value)
      self._End(lambda actual: match, 'to match %r', pattern)
      return match
    else:
      self._End(lambda actual: re.match(pattern, actual),
                'to match %r', pattern)

  def ToEqual(self, expected_value):
    self._End(
        lambda actual: actual == expected_value,
        'to equal %r', expected_value)

  def ToBeTruthy(self):
    self.ToSatisfy(bool, 'to be truthy')

  def ToEndWith(self, suffix):
    self._End(
        lambda actual: actual.endswith(suffix),
        'to end with %r', suffix)

  def ToExist(self):
    self.Not().ToBe(None)

  def ToBe(self, expected_value):
    self._End(
        lambda actual: actual is expected_value,
        'to be %r', expected_value)

  def ToContain(self, expected_value):
    self._End(
        lambda actual: expected_value in actual,
        'to contain %r', expected_value)

  def ToBeIn(self, allowed_values):
    self._End(
        lambda actual: actual in allowed_values,
        'to be a member of %r', allowed_values)

  def _End(self, predicate, predicate_format, *args):
    assert not self.is_complete
    self.is_complete = True
    try:
      ok = bool(predicate(self.actual_value))
    except:
      ok = False
    if ok != self.want_ok:
      self._Fail(predicate_format, *args)

  def _Fail(self, predicate_format, *args):
    message = 'expected %r%s%s' % (
        self.actual_value,
        ' ' if self.want_ok else ' not ',
        predicate_format % args)
    self.report_error(message)


class TestCaseExpectation(Expectation):

  def __init__(self, value, test_case):
    Expectation.__init__(self, value, test_case.fail)
    self._test_cast = test_case


class TestCase(unittest.TestCase):

  def Expect(self, value):
    return TestCaseExpectation(value, self)
