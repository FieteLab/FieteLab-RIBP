"""
Launch run_one.py with each configuration of the hyperparameters.

Example usage:

01_linear_gaussian/run_all.py
"""

import itertools
import joblib
import logging
import numpy as np
import os
import subprocess

import plot_linear_gaussian
import utils.data_synthetic


def run_all():
    # create directory
    exp_dir_path = '01_linear_gaussian'
    results_dir_path = os.path.join(exp_dir_path, 'results')
    os.makedirs(results_dir_path, exist_ok=True)

    feature_samplings = [
        # ('categorical', dict(probs=np.ones(5) / 5.)),
        ('categorical', dict(probs=np.array([0.4, 0.25, 0.2, 0.1, 0.05]))),
        ('IBP', dict(alpha=1.17, beta=0.58)),
        ('IBP', dict(alpha=1.17, beta=2.4)),
        # ('IBP', dict(alpha=5.98, beta=2.4)),
    ]

    num_datasets = 2
    gaussian_cov_scaling: float = 0.3
    gaussian_mean_prior_cov_scaling: float = 100.
    num_customers = 30

    alphas = np.round(np.linspace(1.1, 5.91, 5), 2)
    betas = np.round(np.linspace(0.3, 8.7, 5), 2)
    inference_alg_strs = ['R-IBP', 'HMC-Gibbs']
    hyperparams = [alphas, betas, inference_alg_strs]

    # generate several datasets and independently launch inference
    for (indicator_sampling, indicator_sampling_params), dataset_idx in \
            itertools.product(feature_samplings, range(num_datasets)):

        logging.info(f'Sampling: {indicator_sampling}, Dataset Index: {dataset_idx}')
        sampled_linear_gaussian_data = utils.data_synthetic.sample_from_linear_gaussian(
            num_obs=num_customers,
            indicator_sampling=indicator_sampling,
            indicator_sampling_params=indicator_sampling_params,
            gaussian_prior_params=dict(gaussian_cov_scaling=gaussian_cov_scaling,
                                       gaussian_mean_prior_cov_scaling=gaussian_mean_prior_cov_scaling))

        # save dataset
        run_one_results_dir_path = os.path.join(
            results_dir_path,
            sampled_linear_gaussian_data['indicator_sampling_descr_str'],
            f'dataset={dataset_idx}')
        os.makedirs(run_one_results_dir_path, exist_ok=True)
        joblib.dump(sampled_linear_gaussian_data,
                    filename=os.path.join(run_one_results_dir_path, 'data.joblib'))

        plot_linear_gaussian.plot_sample_from_linear_gaussian(
            features=sampled_linear_gaussian_data['features'],
            observations=sampled_linear_gaussian_data['observations'],
            plot_dir=run_one_results_dir_path)

        for alpha, beta, inference_alg_str in itertools.product(*hyperparams):
            launch_run_one(
                exp_dir_path=exp_dir_path,
                run_one_results_dir_path=run_one_results_dir_path,
                inference_alg_str=inference_alg_str,
                alpha=alpha,
                beta=beta)
            # continue


def launch_run_one(exp_dir_path: str,
                   run_one_results_dir_path: str,
                   inference_alg_str: str,
                   alpha: float,
                   beta: float):

    run_one_script_path = os.path.join(exp_dir_path, 'run_one.sh')
    command_and_args = [
        'sbatch',
        run_one_script_path,
        run_one_results_dir_path,
        inference_alg_str,
        str(alpha),
        str(beta)]

    # TODO: Figure out where the logger is logging to
    logging.info(f'Launching ' + ' '.join(command_and_args))
    subprocess.run(command_and_args)
    logging.info(f'Launched ' + ' '.join(command_and_args))


if __name__ == '__main__':
    run_all()
    logging.info('Finished.')
