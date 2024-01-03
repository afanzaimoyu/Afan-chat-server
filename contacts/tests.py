from collections import OrderedDict

from django.test import TestCase

# Create your tests here.
a = OrderedDict(next_cursor=1, is_last=2, display_records=3)
print(a)