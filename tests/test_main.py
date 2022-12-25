import json
import logging
import os
import unittest
from argparse import Namespace

import main


class MainTest(unittest.TestCase):
    def test_parse_args(self):
        """
        If no args used,
        script still got necessary vars in None
        """
        self.assertEqual(main.parse_args(), Namespace(file=None, key=None))

    def test_get_json(self):
        """
        Positive scenarios of main.get_json()
        case1: specific path to the file is provided
        case2: path to the file is absent
        case3: url to json_data is provided
        """
        with open('template.json') as file:
            template = json.load(file)
        url = 'https://s3.eu-west-3.amazonaws.com/elmariachi.bucket/test.json'
        self.assertEqual(main.get_json('template.json'), (template, 'template.json'))
        self.assertEqual(main.get_json(), (template, 'template.json'))
        self.assertEqual(main.get_json(url), (template, 'info_from_url.json'))

    def test_get_json_fails(self):
        """
        Negative scenarios of main.get_json()
        Check sys.exit() is called and proper message exists in log

        case1: more than 1 json file in current_dir and no file.args used
        case2: provided file not in JSON format
        case3: provided file does not exist
        case4: data received by url not in JSON format
        case5: provided host with JSON info is unavailable
        """
        with open('extra.json', 'w') as extra:
            extra.write('ExtraJSON')
        url = 'https://s3.eu-west-3.amazonaws.com/elmariachi.bucket/'
        with self.assertLogs(level=logging.ERROR) as more_than_one, self.assertRaises(SystemExit):
            main.get_json()
        with self.assertLogs(level=logging.ERROR) as not_json, self.assertRaises(SystemExit):
            main.get_json('extra.json')
        with self.assertLogs(level=logging.ERROR) as no_file, self.assertRaises(SystemExit):
            main.get_json('template.json2')
        with self.assertLogs(level=logging.ERROR) as wrong_url, self.assertRaises(SystemExit):
            main.get_json(url)
        with self.assertLogs(level=logging.ERROR) as conn_err, self.assertRaises(SystemExit):
            main.get_json(url.replace('.amazonaws.', '.'))
        self.assertIn('Found more than 1', more_than_one.output[0])
        self.assertIn('is not in JSON format', not_json.output[0])
        self.assertIn('does not exist', no_file.output[0])
        self.assertIn('is not in JSON format', wrong_url.output[0])
        self.assertIn('Connection to "{}" failed'
                      .format(url.replace('.amazonaws.', '.')),
                      conn_err.output[0])
        os.remove('extra.json')

    def test_get_json_empty(self):
        """
        Negative scenario of main.get_json()
        No *.json file exists in current directory and no file.args provided
        Check sys.exit() is called and proper message exists in log
        """
        template = 'template.json'
        new_name = 'template.txt'
        os.rename(template, new_name)
        with self.assertLogs(level=logging.ERROR) as no_file, self.assertRaises(SystemExit):
            main.get_json()
        os.rename(new_name, template)
        self.assertIn('No JSON file found', no_file.output[0])


if __name__ == '__main__':
    unittest.main()
