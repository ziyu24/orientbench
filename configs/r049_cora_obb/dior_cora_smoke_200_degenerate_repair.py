_base_ = './dior_cora_smoke_200.py'

# Fast numerical verification of the registered annotation hygiene repair. The
# complete smoke configuration retains full validation in its parent file.
train_cfg = dict(_delete_=True, type='IterBasedTrainLoop', max_iters=200, val_interval=100000)
