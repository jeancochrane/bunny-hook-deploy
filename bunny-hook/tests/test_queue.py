import os
import sqlite3
from unittest import TestCase
from unittest.mock import patch

import env
from api.queue import Queue


class TestQueue(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_conn = 'test.db'
        cls.queue = Queue(cls.db_conn)

        cls.payload = {
            'ref': 'refs/head/master',
            'repository': {
                'name': 'bunny-hook'
            },
            'clone_url': 'https://github.com/jeancochrane/bunny-hook.git'
        }

    @classmethod
    def tearDownClass(cls):
        os.remove('test.db')

    def tearDown(self):
        self.queue.cursor.execute('DELETE FROM queue')

    def test_queue_created(self):
        create_table = '''
            CREATE TABLE queue
                (id TEXT, payload TEXT, date_added NUMERIC)
        '''

        with self.assertRaises(sqlite3.OperationalError) as exc:
            queue_table = self.queue.cursor.execute(create_table)

    def test_queue_add(self):
        work_id = self.queue.add(self.payload)

        queue = self.queue.cursor.execute('''
            SELECT *
            FROM queue
            WHERE id = ?
        ''', (work_id,)).fetchone()

        self.assertTrue(len(queue) > 0)

    def test_queue_pop(self):
        self.queue.add(self.payload)

        work = self.queue.pop()
        self.assertTrue(work == self.payload)

    def test_queue_pop_no_work(self):
        self.assertIsNone(self.queue.pop())

    def test_queue_add_commits_to_database(self):
        work_id = self.queue.add(self.payload)

        # Open a separate queue connection
        second_queue = Queue(self.db_conn)

        # Check that work is queryable from the second queue
        work = second_queue.pop()

        self.assertIsNotNone(work)
        self.assertEqual(work, self.payload)

    @patch('api.queue.Worker.deploy')
    def test_queue_run(self, mock_deploy):
        self.queue.add(self.payload)

        # Check that work was added to the queue
        queue = self.queue.cursor.execute('SELECT * FROM queue').fetchall()
        self.assertTrue(len(queue) > 0)

        self.queue.run()

        # Check that `Worker.deploy` was called, and work was removed from the
        # queue
        self.assertTrue(mock_deploy.called)
        self.assertIsNone(self.queue.pop())

