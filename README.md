# prometheus_client_concurrency_issue

Disclaimer: this script reproduces a bug that results in metrics reporting completely broken.
It runs in multiprocessing environment, after the bug occurs one of the db files is corrupted and the state is inrecoverable.

This script is a shrunk down version of a production script that does actual work. It mimics how processes are created and destroyed in the original script. 

## How to reproduce?

### Environment

Create virtualenv:

```
mkvirtualenv metrics-issue27 --python python2.7
```

Install requirements:

```
pip install -r requirements.txt
```

### Experiment

The bug reproduces not 100% of the time since it is a sort of concurrency issue.

To be able to reproduce one should repeat, maybe several times, this procedure:

1. run the script:
```
prometheus_multiproc_dir=./tmp/ python -u ./reproduce.py 928453 2>&1 | tee output.log
```
2. wait ~5s, until it prints `RECONFIGURE` a couple of times
3. go to the browser and open http://localhost:8000
4. if there is no error in the browser nor in the logs, go back to 3) a few times
5. if there is an error like below, finish: reproduction succeeded
6. if did not reproduce, after ~15s stop this attempt and try from 1)

The stdout will look like this:

```
$ prometheus_multiproc_dir=./tmp/ python -u ./reproduce.py 928453 2>&1 | tee output.log
INFO:root:Starting up
INFO:root:MAIN
RANDOM SEED: 928453
INFO:root:Exposing prometheus metrics in multi-process mode
INFO:root:Cleaning up prometheus multiprocessing dir: ./tmp/
INFO:root:Starting 0 process
INFO:root:Starting 1 process
INFO:root:Starting 2 process
INFO:root:Starting 3 process
INFO:root:Starting 4 process
INFO:root:Starting 5 process
INFO:root:Starting 6 process
INFO:root:Sleep for 0.46
INFO:root:Sleep for 0.385
INFO:root:RECONFIGURE!
INFO:root:Reconfigure with writers: [6, 1, 2, 5]
INFO:root:Starting 6 process
INFO:root:Starting 1 process
INFO:root:Starting 2 process
INFO:root:Starting 5 process
INFO:root:Sleep for 0.498
INFO:root:RECONFIGURE!
INFO:root:Reconfigure with writers: [5]
INFO:root:Starting 5 process
INFO:root:Sleep for 0.437
INFO:root:RECONFIGURE!
INFO:root:Reconfigure with writers: [0, 1, 2, 6, 3, 4]
INFO:root:Starting 0 process
INFO:root:Starting 1 process
INFO:root:Starting 2 process
```

### Possible error messages

It seems that the `.db` file with the metrics gets corrupted, hence the error messages
are not consistent and are mainly deserializaion errors.

Here are possible error messages:

```
Process Process-7:
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/multiprocessing/process.py", line 267, in _bootstrap
Process Process-5:
    self.run()
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/multiprocessing/process.py", line 114, in run
Traceback (most recent call last):
    self._target(*self._args, **self._kwargs)
  File "./reproduce.py", line 56, in serve
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/multiprocessing/process.py", line 267, in _bootstrap
    self.my_gauge.labels("my label").set(10000)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 784, in labels
    self.run()
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/multiprocessing/process.py", line 114, in run
    self._target(*self._args, **self._kwargs)
  File "./reproduce.py", line 56, in serve
    self.my_gauge.labels("my label").set(10000)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 784, in labels
    **self._kwargs
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 973, in __init__
    multiprocess_mode=multiprocess_mode)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 669, in __init__
    self.__reset()
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 682, in __reset
    files[file_prefix] = _MmapedDict(filename)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 577, in __init__
    for key, _, pos in self._read_all_values():
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 611, in _read_all_values
    encoded = unpack_from(('%ss' % encoded_len).encode(), data, pos)[0]
    **self._kwargs
error: unpack_from requires a buffer of at least 1919251561 bytes
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 973, in __init__
    multiprocess_mode=multiprocess_mode)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 669, in __init__
    self.__reset()
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 682, in __reset
    files[file_prefix] = _MmapedDict(filename)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 577, in __init__
    for key, _, pos in self._read_all_values():
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 611, in _read_all_values
    encoded = unpack_from(('%ss' % encoded_len).encode(), data, pos)[0]
error: unpack_from requires a buffer of at least 1919251561 bytes
```

You may find the state of the db files (zipped) after seeing this message in `./error1` folder.

```
----------------------------------------
Exception happened during processing of request from ('127.0.0.1', 62123)
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/SocketServer.py", line 596, in process_request_thread
    self.finish_request(request, client_address)
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/SocketServer.py", line 331, in finish_request
    self.RequestHandlerClass(request, client_address, self)
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/SocketServer.py", line 652, in __init__
    self.handle()
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/BaseHTTPServer.py", line 340, in handle
    self.handle_one_request()
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/BaseHTTPServer.py", line 328, in handle_one_request
    method()
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/exposition.py", line 145, in do_GET
    output = encoder(registry)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/exposition.py", line 88, in generate_latest
    for metric in registry.collect():
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/core.py", line 147, in collect
    for metric in collector.collect():
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/multiprocess.py", line 27, in collect
    return self.merge(files, accumulate=True)
  File "/Users/vasiliev/.virtualenvs/metrics-issue27/lib/python2.7/site-packages/prometheus_client/multiprocess.py", line 42, in merge
    metric_name, name, labels = json.loads(key)
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/json/__init__.py", line 339, in loads
    return _default_decoder.decode(s)
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/json/decoder.py", line 364, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
  File "/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/json/decoder.py", line 382, in raw_decode
    raise ValueError("No JSON object could be decoded")
ValueError: No JSON object could be decoded
----------------------------------------
```

You may find the state of the db files (zipped) after seeing this message in `./error2` folder.
