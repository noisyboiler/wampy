from ... messages.call import Call
from ... peer import ClientBase


class StandAloneClient(ClientBase):

    def make_rpc(self, procedure):
        message = Call(procedure=procedure)
        message.construct()
        self._send(message)
        response = self._recv()
        result = response[3]
        return result[0]
