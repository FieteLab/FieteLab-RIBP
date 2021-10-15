"""
Launch run_one.py with each configuration of the hyperparameters.

Example usage:

03_omniglot/run_all.py
"""

import itertools
import logging
import numpy as np
import os
import subprocess


def run_all() -> None:
    # create directory
    exp_dir_path = '03_omniglot'
    results_dir_path = os.path.join(exp_dir_path, 'results')
    os.makedirs(results_dir_path, exist_ok=True)

    alphas = np.round(np.arange(1., 5.01, 1.), 4)
    betas = np.round(np.arange(1., 11.01, 1.), 4)[::-1]
    sigma_xs = np.round(np.logspace(-2, 0, 5), 4)
    feature_prior_cov_scalings = np.round(np.logspace(0., 2., 3), 4)[::-1]
    scale_prior_cov_scalings = np.round(np.logspace(0., 2., 4), 4)[::-1]
    inference_alg_strs = [
        'R-IBP',
    ]
    hyperparams = [
        alphas,
        betas,
        sigma_xs,
        feature_prior_cov_scalings,
        scale_prior_cov_scalings,
        inference_alg_strs,
    ]

    counter = 0
    for alpha, beta, sigma_x, feature_prior_cov_scaling, scale_prior_cov_scaling,\
        inference_alg_str in itertools.product(*hyperparams):

        run_str = f'{inference_alg_str}_a={alpha}_b={beta}_' \
                                f'sigmax={sigma_x}_featurecov={feature_prior_cov_scaling}_' \
                                f'scalecov={scale_prior_cov_scaling}'

        run_one_results_dir_path = os.path.join(
            results_dir_path,
            run_str)

        launch_run_one(
            exp_dir_path=exp_dir_path,
            run_one_results_dir_path=run_one_results_dir_path,
            inference_alg_str=inference_alg_str,
            alpha=alpha,
            beta=beta,
            sigma_x=sigma_x,
            feature_prior_cov_scaling=feature_prior_cov_scaling,
            scale_prior_cov_scaling=scale_prior_cov_scaling)

        counter += 1
        if counter == 1000:
            break


def launch_run_one(exp_dir_path: str,
                   run_one_results_dir_path: str,
                   inference_alg_str: str,
                   alpha: float,
                   beta: float,
                   sigma_x: float,
                   feature_prior_cov_scaling: float,
                   scale_prior_cov_scaling: float) -> None:

    run_one_script_path = os.path.join(exp_dir_path, 'run_one.sh')
    command_and_args = [
        'sbatch',
        run_one_script_path,
        run_one_results_dir_path,
        inference_alg_str,
        str(alpha),
        str(beta),
        str(sigma_x),
        str(feature_prior_cov_scaling),
        str(scale_prior_cov_scaling),
        ]

    # TODO: Figure out where the logger is logging to
    logging.info(f'Launching ' + ' '.join(command_and_args))
    subprocess.run(command_and_args)
    logging.info(f'Launched ' + ' '.join(command_and_args))


if __name__ == '__main__':
    run_all()
    logging.info('Finished.')
