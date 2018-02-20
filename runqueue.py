from api.queue import Queue


if __name__ == '__main__':
    queue = Queue()

    # Run the queue in an endless loop
    while True:
        queue.run()
