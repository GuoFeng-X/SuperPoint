import numpy as np
import os
import argparse
import yaml
from pathlib import Path
from tqdm import tqdm

import experiment
from superpoint.settings import EXPER_PATH

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str)
    parser.add_argument('experiment_name', type=str)
    parser.add_argument('--export_name', type=str, default=None)
    parser.add_argument('--pred_only', action='store_true')
    args = parser.parse_args()

    experiment_name = args.experiment_name
    export_name = args.export_name if args.export_name else experiment_name
    with open(args.config, 'r') as f:
        config = yaml.load(f)
    assert 'eval_iter' in config

    output_dir = Path(EXPER_PATH, 'outputs/{}/'.format(export_name))
    if not output_dir.exists():
        os.makedirs(output_dir)
    checkpoint_dir = Path(EXPER_PATH, experiment_name)

    with experiment._init_graph(config, with_dataset=True) as (net, dataset):
        if net.trainable:
            net.load(str(checkpoint_dir))
        test_set = dataset.get_test_set()

        pbar = tqdm(total=config['eval_iter'] if config['eval_iter'] > 0 else None)
        i = 0
        while True:
            try:
                data = next(test_set)
            except dataset.end_set:
                break
            pred = net.predict(data, keys='*')
            if args.pred_only:
                pred = {'points': np.array(np.where(pred['pred'])).T}
            if not ('name' in data):
                pred.update(data)
            filename = data['name'].decode('utf-8') if 'name' in data else str(i)
            filepath = Path(output_dir, '{}.npz'.format(filename))
            np.savez_compressed(filepath, **pred)
            i += 1
            pbar.update(1)
            if i == config['eval_iter']:
                break
