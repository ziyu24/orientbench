"""Freeze the valid host during the r051 cheap-signal gate."""
from mmengine.hooks import Hook
from mmrotate.registry import HOOKS


@HOOKS.register_module()
class CMRFreezeHostHook(Hook):
    priority = 'VERY_HIGH'

    def before_train(self, runner):
        # DDP constructs its reduction buckets before this hook. Keeping host
        # parameters differentiable avoids unused-parameter divergence; their
        # gradients are removed immediately before every optimizer step, so
        # only CMR can change during the cheap-signal gate.
        runner.logger.info('CMR frozen-host gate: only roi_head.cmr gradients will be stepped')

    def before_optim_wrapper(self, runner, **kwargs):
        for name, parameter in runner.model.named_parameters():
            if not name.removeprefix('module.').startswith('roi_head.cmr.'):
                parameter.grad = None
