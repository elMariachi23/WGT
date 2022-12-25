import json
import os
import unittest
from argparse import Namespace

import main


class MainTest(unittest.TestCase):
    def test_parse_args(self):
        self.assertEqual(main.parse_args(), Namespace(file=None, key=None))

    def test_get_json(self):
        with open('template.json') as file:
            template = json.load(file)
        url = 'https://s3.eu-west-3.amazonaws.com/elmariachi.bucket/test.json'
        self.assertEqual(main.get_json('template.json'), (template, 'template.json'))
        self.assertEqual(main.get_json(), (template, 'template.json'))
        self.assertEqual(main.get_json(url), (template, 'info_from_url.json'))

    def test_get_json_fails(self):
        with open('extra.json', 'w') as extra:
            extra.write('ExtraJSON')
        url = 'https://s3.eu-west-3.amazonaws.com/elmariachi.bucket/'
        with self.assertRaises(SystemExit) as more_than_one:
            main.get_json()
        with self.assertRaises(SystemExit) as not_json:
            main.get_json('extra.json')
        with self.assertRaises(SystemExit) as no_file:
            main.get_json('template.json2')
        with self.assertRaises(SystemExit) as wrong_url:
            main.get_json(url)
        with self.assertRaises(SystemExit) as conn_err:
            main.get_json(url.replace('.amazonaws.', '.'))
        self.assertIn('Found more than 1', str(more_than_one.exception))
        self.assertIn('is not in JSON format', str(not_json.exception))
        self.assertIn('does not exist', str(no_file.exception))
        self.assertIn('is not in JSON format', str(wrong_url.exception))
        self.assertIn('Connection to "{}" failed'
                      .format(url.replace('.amazonaws.', '.')),
                      str(conn_err.exception))
        os.remove('extra.json')

    def test_get_json_empty(self):
        template = 'template.json'
        new_name = 'template.txt'
        os.rename(template, new_name)
        with self.assertRaises(SystemExit) as no_file:
            main.get_json()
        self.assertIn('No JSON file found', str(no_file.exception))
        os.rename(new_name, template)


if __name__ == '__main__':
    unittest.main()
