from wampy.messages.register import Register


class CalleeMixin(object):

    def register(self, procedure_name):
        message = Register(procedure=procedure_name)

        response_msg = self.send_message_and_wait_for_response(message)
        _, _, registration_id = response_msg

        self.registration_map[procedure_name] = registration_id

        self.logger.info(
            'registering entrypoint "%s" for callee "%s"',
            procedure_name, self.name
        )


def register_callee(wrapped):
    def decorator(fn):
        fn.rpc = True
        return fn

    return decorator(wrapped)


rpc = register_callee
