#!/bin/python3
# author: Jan Hybs

import tests

from unittest import TestCase
from utils import colors


class TestColors(TestCase):
    def test_hex2rgb(self):
        self.assertTupleEqual(colors.hex2rgb('#FF0000'), (255, 0, 0))
        self.assertTupleEqual(colors.hex2rgb('#00FF00'), (0, 255, 0))
        self.assertTupleEqual(colors.hex2rgb('#0000FF'), (0, 0, 255))

        self.assertTupleEqual(colors.hex2rgb('#009BFF'), (0, 155, 255))
        self.assertTupleEqual(colors.hex2rgb('#000000'), (0, 0, 0))
        self.assertTupleEqual(colors.hex2rgb('#ffFFff'), (255, 255, 255))

    def test_rgb2hex(self):
        self.assertEqual(colors.rgb2hex((255, 0, 0)), '#FF0000'.lower())
        self.assertEqual(colors.rgb2hex((0, 255, 0)), '#00FF00'.lower())
        self.assertEqual(colors.rgb2hex((0, 0, 255)), '#0000FF'.lower())

        self.assertEqual(colors.rgb2hex((0, 155, 255)), '#009BFF'.lower())
        self.assertEqual(colors.rgb2hex((0, 0, 0)), '#000000'.lower())
        self.assertEqual(colors.rgb2hex((255, 255, 255)), '#ffFFff'.lower())

    def test_rgb2html(self):
        self.assertEqual(colors.rgb2html((255, 0, 0)), 'rgb(255, 0, 0)')
        self.assertEqual(colors.rgb2html((0, 255, 0)), 'rgb(0, 255, 0)')
        self.assertEqual(colors.rgb2html((0, 0, 255)), 'rgb(0, 0, 255)')

        self.assertEqual(colors.rgb2html((0, 155, 255)), 'rgb(0, 155, 255)')
        self.assertEqual(colors.rgb2html((0, 0, 0)), 'rgb(0, 0, 0)')
        self.assertEqual(colors.rgb2html((255, 255, 255)), 'rgb(255, 255, 255)')

        self.assertEqual(colors.rgb2html((255, 255, 255), 0.5), 'rgba(255, 255, 255, 0.50)')
        self.assertEqual(colors.rgb2html((255, 255, 255), 0.125), 'rgba(255, 255, 255, 0.12)')

    def test_configurable_html_color(self):
         lambda_func = colors.configurable_html_color((255, 255, 255))
         self.assertEqual(lambda_func(0.5), 'rgba(255, 255, 255, 0.50)')
         self.assertEqual(lambda_func(0.13), 'rgba(255, 255, 255, 0.13)')
         self.assertEqual(lambda_func(None), 'rgb(255, 255, 255)')
