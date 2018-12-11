#!/bin/python3
# author: Jan Hybs


class AbstractWebhookTrigger(object):

    def process(self, payload):
        """
        Parameters
        ----------
        payload: cihpc.common.utils.git.webhooks.push_hook.PushWebhook
            payload to process

        Returns
        -------
        bool
            True on success False otherwise
        """
        raise NotImplementedError('Not implemented!')

    def wait(self):
        raise NotImplementedError('Not implemented!')
