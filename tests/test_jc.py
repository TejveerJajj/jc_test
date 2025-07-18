import unittest
from unittest.mock import patch, MagicMock
import jc

class TestJc(unittest.TestCase):

    def setUp(self):
        # Define the variables that are missing
        jc.STATUS_URL = "http://fake-elk-url.com/_cluster/health?pretty=true"
        jc.ACTION_URL = "http://fake-elk-url.com/_watcher/watch/"
        jc.REQ_HEADERS = {'content-type': 'application/json'}
        jc.username = "testuser"
        jc.password = "testpass"

    @patch('jc.get_local_watch_id_dict')
    def test_get_local_watch_id_list(self, mock_get_local_watch_id_dict):
        mock_get_local_watch_id_dict.return_value = {'watch1': '/path/to/watch1', 'watch2': '/path/to/watch2'}
        self.assertEqual(jc.get_local_watch_id_list(), ['watch1', 'watch2'])

    @patch('builtins.open')
    @patch('json.loads')
    def test_parse_es_to_json(self, mock_json_loads, mock_open):
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.readlines.return_value = ['line1', 'line2']
        jc.parse_es_to_json('/fake/dir')
        mock_json_loads.assert_called()

    @patch('requests.get')
    def test_check_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = '{"status": "green"}'
        mock_get.return_value = mock_response
        jc.check_status()
        mock_get.assert_called()

    @patch('requests.put')
    def test_activate_watch(self, mock_put):
        jc.activate_watch('test_watch')
        mock_put.assert_called()

    @patch('requests.put')
    def test_deactivate_watch(self, mock_put):
        mock_response = MagicMock()
        mock_response.content = '{"acknowledged": true}'
        mock_put.return_value = mock_response
        jc.deactivate_watch('test_watch')
        mock_put.assert_called()

    @patch('requests.delete')
    def test_delete_watch(self, mock_delete):
        mock_response = MagicMock()
        mock_response.content = '{"found": true}'
        mock_delete.return_value = mock_response
        jc.delete_watch('test_watch')
        mock_delete.assert_called()

if __name__ == '__main__':
    unittest.main()
