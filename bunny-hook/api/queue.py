# queue.py -- run tasks from a queue
import sqlite3
import time
import json
from uuid import uuid4

from api.worker import Worker


class Queue(object):
    '''
    Create and manage a queue of deployment jobs. This class bridges the API
    and the Worker, so that deployment doesn't have to be attached to the
    request/response cycle.
    '''
    # Default SQLite connection string
    db_conn = 'hook.db'

    def __init__(self, db_conn=None):
        '''
        Initialize a connection to the datastore.

        Args:
            - db_conn (string): Optional SQLite connection string, if the class
                                should use a different datastore.
        '''
        if db_conn:
            self.db_conn = db_conn

        self.conn = sqlite3.connect(self.db_conn)
        self.cursor = self.conn.cursor()

        # Create a table for the queue if it doesn't exist
        create_table = '''
            CREATE TABLE IF NOT EXISTS queue
                (id TEXT, payload TEXT, date_added NUMERIC)
        '''
        self.cursor.execute(create_table)

    def add(self, payload):
        '''
        Package up a work payload and drop it into the queue. Returns the ID
        of the queued work.

        Args:
            - payload (dict): An event from the GitHub API.
        '''
        work_id = str(uuid4())

        insert = '''
            INSERT INTO queue
                     (id, payload, date_added)
              VALUES (?, ?, ?)
        '''
        self.cursor.execute(insert, (work_id, json.dumps(payload), time.time()))

        self.conn.commit()

        return work_id

    def pop(self):
        '''
        Return the most recent payload and remove it from the queue.
        '''
        # Start a transaction for the duration of the write
        self.cursor.execute('BEGIN TRANSACTION')

        self.cursor.execute('SELECT * FROM queue ORDER BY date_added LIMIT 1')
        work = self.cursor.fetchone()

        if work:
            work_id = work[0]
            payload = json.loads(work[1])

            # Delete the job from the queue
            self.cursor.execute('DELETE FROM queue WHERE id = ?', (work_id,))
        else:
            # No work was found in the queue
            payload = None

        self.conn.commit()

        return payload

    def run(self):
        '''
        Check for work on the queue, and if it exists, deploy it.
        '''
        payload = self.pop()
        if payload:
            worker = Worker(payload)
            worker.deploy()
