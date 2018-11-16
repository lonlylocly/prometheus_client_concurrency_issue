import glob
import logging
import logging.config
import os
import random
import copy

from time import sleep
import sys

import prometheus_client
import prometheus_client.multiprocess
from multiprocessing import Process
from prometheus_client import Gauge


# prometheus_multiproc_dir=./tmp/ python -u ./reproduce.py 928453 2>&1 | tee output.log
# protocol:
# - run cmd above
# - wait 5 s
# - open localhost:8000 few times
# - stop when 30 s total
# outcome: managed to reproduce in 30 s or not?


BATCH_SIZE = 1000
SENTRY_ENV_VAR = 'SENTRY_DSN'
PROM_METRICS_ENDPOINT_PORT = 8000

RANDOM_SEED = random.randint(1, 1000000)

logging.basicConfig(level=logging.INFO)


class Writer():

    def __init__(self, worker_id):
        self.worker_id = worker_id
        self._prom_name = "writer_{}".format(worker_id)
        self.processed_count = 0

    def serve(self):
        self.my_gauge = Gauge('{}_my_gauge'.format(self._prom_name), 'My awesome gauge', ['label1'])
        while True:
            inc_val = 10 + random.randint(1, 10)
            self.processed_count += inc_val

            self.my_gauge.labels("my label").set(10000)
            self.processed_count = 0
            sleep(0.05)


def setup_prom_server():
    multiproc_dir = os.environ['prometheus_multiproc_dir']
    logging.info("Exposing prometheus metrics in multi-process mode")
    logging.info("Cleaning up prometheus multiprocessing dir: {}".format(multiproc_dir))
    for f in glob.glob(os.path.join(multiproc_dir, '*.db')):
        os.remove(f)
    registry = prometheus_client.CollectorRegistry()
    prometheus_client.multiprocess.MultiProcessCollector(registry)
    prometheus_client.start_http_server(PROM_METRICS_ENDPOINT_PORT, registry=registry)


def _init_and_start_writers(writer_nums):
    writers = []

    for w in writer_nums:
        writers.extend([
            Writer(
                worker_id=w
            )
        ])

    writer_processes = [
        Process(target=w.serve)
        for w in writers
    ]

    for i, writer_process in enumerate(writer_processes):
        logging.info("Starting {} process".format(writers[i].worker_id))
        writer_process.start()

    return writers, writer_processes


def start_writers():

    writer_nums = list(range(0, 7))

    writers, writer_processes = _init_and_start_writers(
        writer_nums
    )

    # Prometheus metrics
    writer_process_metric = Gauge("writer_process_count", "number of active writer processes", ['worker_id'])

    while True:
        for i, process in enumerate(writer_processes):
            writer_process_metric.labels(writers[i].worker_id).set(int(process.is_alive()))

            # imitate context switching caused by IO
            sleep(0.01)

        if random.randint(1, 100) < 50:
            logging.info("RECONFIGURE!")
            for i, process in enumerate(writer_processes):
                process.terminate()
                process.join()

            new_writers = copy.copy(writer_nums)
            random.shuffle(new_writers)
            new_writers_len = random.randint(1, len(new_writers))
            logging.info("Reconfigure with writers: {}".format(new_writers[:new_writers_len]))
            writers, writer_processes = _init_and_start_writers(
                new_writers[:new_writers_len]
            )
        sleep_int = random.randint(300, 500) / 1000.
        logging.info("Sleep for %s"%sleep_int)
        sleep(sleep_int)


def main():
    logging.info("MAIN")

    global RANDOM_SEED
    if len(sys.argv) > 1:
        RANDOM_SEED = int(sys.argv[1])
    print("RANDOM SEED: {}".format(RANDOM_SEED))

    random.seed(RANDOM_SEED)

    setup_prom_server()

    start_writers()


if __name__ == "__main__":
    logging.info("Starting up")
    main()
