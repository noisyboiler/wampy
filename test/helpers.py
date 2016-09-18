import eventlet


def assert_stops_raising(
        fn, exception_type=Exception, timeout=5, interval=0.1):

    with eventlet.Timeout(timeout):
        while True:
            try:
                fn()
            except exception_type:
                pass
            else:
                return
            eventlet.sleep(interval)
