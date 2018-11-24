#!/bin/python3
# author: Jan Hybs

import tests

import yaml
from os.path import join
from unittest import TestCase

from cihpc.cfg.cfgutil import read_file
from cihpc.vcs.webhooks.push_hook import push_webhook_from_dict, push_webhook_to_dict

webhook_dir = join(tests.__dir__, 'webhooks')
content = read_file(join(webhook_dir, 'example.json'))
yaml_file = yaml.load(content)


class TestPush_webhook(TestCase):

    def test_push_webhook_to_dict(self):
        webhook = push_webhook_from_dict(yaml_file)
        dictionary = push_webhook_to_dict(webhook)

        self.assertEqual(dictionary['head_commit']['author']['username'], 'janhybs')
        self.assertIsInstance(dictionary['commits'], list)
        self.assertEqual(dictionary['commits'][0]['timestamp'], '2018-11-19T08:53:54+01:00')
        self.assertEqual(dictionary['after'], 'e87eead22e741dafb58355b9a6cbcd632c8f3704')

    def test_push_webhook_from_dict(self):
        webhook = push_webhook_from_dict(yaml_file)

        self.assertEqual(webhook.head_commit.author.username, 'janhybs')
        self.assertIsInstance(webhook.commits, list)
        self.assertEqual(webhook.commits[0].message, 'Change L3 array size from 32 to 44')
        self.assertEqual(webhook.commits[0].distinct, True)
        self.assertEqual(webhook.after, 'e87eead22e741dafb58355b9a6cbcd632c8f3704')
