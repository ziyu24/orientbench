"""Freeze the valid host during the r051 cheap-signal gate."""
from mmengine.hooks import Hook
from mmrotate.registry import HOOKS


@HOOKS.register_module()
class CMRFreezeHostHook(Hook):
    priority = 'VERY_HIGH'

    def before_train(self, runner):
        for name, parameter in runner.model.named_parameters():
            parameter.requires_grad_(name.startswith('roi_head.cmr.'))
        trainable = [name for name, p in runner.model.named_parameters() if p.requires_grad]
        if not trainable or any(not name.startswith('roi_head.cmr.') for name in trainable):
            raise RuntimeError('CMR G1 frozen-host invariant failed')
        runner.logger.info('CMR frozen-host gate: trainable=%s', ','.join(trainable))
