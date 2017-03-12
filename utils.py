import time


def retry(max_retries=0, sleep_between_s=0., error_msg="Error",
          failure_msg=None, exception=None):
    def wrapped_decorator(func):
        def wrapped_func(*args, **kwargs):
            _failure_msg = failure_msg
            if _failure_msg is not None:
                _failure_msg = "Failed to {} after {} retries.".format(
                    func.__name__, max_retries)

            tries = 0
            while True:
                tries += 1
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(error_msg, str(e))

                if 0 < max_retries <= tries:
                    if exception is not None:
                        raise exception
                    print(failure_msg)
                    break

                time.sleep(sleep_between_s)
        return wrapped_func
    return wrapped_decorator
