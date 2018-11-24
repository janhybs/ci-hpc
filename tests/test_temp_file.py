#!/bin/python3
# author: Jan Hybs

import tests
import random
from unittest import TestCase
from cihpc.utils.files.temp_file import TempFile


class TestTempFile(TestCase):

    def test_write_shebang(self):
        temp_file = TempFile('foo.sh')

        # forced shebang
        shebang = '#!/bin/sh'
        with temp_file:
            temp_file.write_shebang(shebang)

        self.assertTrue(temp_file.read().startswith(shebang))
        temp_file.remove()

        # default shebang
        shebang = '#!/bin/bash'
        with temp_file:
            temp_file.write_shebang()

        self.assertTrue(temp_file.read().startswith(shebang))
        temp_file.remove()

    def test_read(self):
        temp_file = TempFile('foo.sh')
        value = str(random.random())

        with temp_file:
            temp_file.write(value)

        with open('foo.sh', 'r') as fp:
            self.assertTrue(fp.read().index(value) != -1)
        temp_file.remove()

    def test_write(self):
        temp_file = TempFile('foo.sh')
        value = str(random.random())

        with temp_file:
            temp_file.write(value)
        self.assertTrue(temp_file.read().index(value) != -1)
        temp_file.remove()
