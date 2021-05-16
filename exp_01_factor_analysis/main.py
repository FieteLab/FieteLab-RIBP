import joblib
import os
from timeit import default_timer as timer

from exp_01_binary_linear_gaussian.plot import *
import utils.data
import utils.inference
import utils.metrics
import utils.plot


def main():
    plot_dir = 'exp_01_binary_linear_gaussian/plots'
    os.makedirs(plot_dir, exist_ok=True)
    np.random.seed(1)

    num_datasets = 10
    inference_algs_results_by_dataset_idx = {}
    sampled_mog_results_by_dataset_idx = {}

    # generate lots of datasets and record performance for each
    for dataset_idx in range(num_datasets):
        print(f'Dataset Index: {dataset_idx}')
        dataset_dir = os.path.join(plot_dir, f'dataset={dataset_idx}')
        os.makedirs(dataset_dir, exist_ok=True)
        dataset_inference_algs_results, dataset_sampled_binary_linear_gaussians_results = run_one_dataset(
            dataset_dir=dataset_dir)
        inference_algs_results_by_dataset_idx[dataset_idx] = dataset_inference_algs_results
        sampled_mog_results_by_dataset_idx[dataset_idx] = dataset_sampled_binary_linear_gaussians_results

    utils.plot.plot_inference_algs_comparison(
        plot_dir=plot_dir,
        inference_algs_results_by_dataset_idx=inference_algs_results_by_dataset_idx,
        dataset_by_dataset_idx=sampled_mog_results_by_dataset_idx)

    print('Successfully completed Exp 01 Mixture of Gaussians')


def run_one_dataset(dataset_dir,
                    num_gaussians: int = 3,
                    gaussian_cov_scaling: float = 0.3,
                    gaussian_mean_prior_cov_scaling: float = 6.):

    # sample data
    sampled_binary_linear_gaussian_results = utils.data.sample_sequence_from_binary_linear_gaussian(
        seq_len=100,
        sigma_A=100.94,
        sigma_x_squared=0.0001,
        obs_dim=2,
        num_latent_features=7)

    concentration_params = 0.01 + np.arange(0., 6.01, 0.25)

    inference_alg_strs = [
        # online algorithms
        'R-IBP',
        # 'SUSG',  # deterministically select highest table assignment posterior
        # 'Online CRP',  # sample from table assignment posterior; potentially correct
        # offline algorithms
        # 'HMC-Gibbs (5000 Samples)',
        # 'HMC-Gibbs (20000 Samples)',
        # 'SVI (25k Steps)',
        # 'SVI (50k Steps)',
        # 'Variational Bayes (15 Init, 30 Iter)',
        # 'Variational Bayes (5 Init, 30 Iter)',
        # 'Variational Bayes (1 Init, 8 Iter)',
    ]

    inference_algs_results = {}
    for inference_alg_str in inference_alg_strs:
        inference_alg_results = run_and_plot_inference_alg(
            sampled_binary_linear_gaussian_results=sampled_binary_linear_gaussian_results,
            inference_alg_str=inference_alg_str,
            concentration_params=concentration_params,
            plot_dir=dataset_dir)
        inference_algs_results[inference_alg_str] = inference_alg_results
    return inference_algs_results, sampled_binary_linear_gaussian_results


def run_and_plot_inference_alg(sampled_binary_linear_gaussian_results,
                               inference_alg_str,
                               concentration_params,
                               plot_dir):

    inference_alg_plot_dir = os.path.join(plot_dir, inference_alg_str)
    os.makedirs(inference_alg_plot_dir, exist_ok=True)
    num_clusters_by_concentration_param = {}
    scores_by_concentration_param = {}
    runtimes_by_concentration_param = {}

    for concentration_param in concentration_params:

        inference_alg_results_concentration_param_path = os.path.join(
            inference_alg_plot_dir,
            f'results_{np.round(concentration_param, 2)}.joblib')

        # if results do not exist, generate
        if not os.path.isfile(inference_alg_results_concentration_param_path):

            # run inference algorithm
            # time using timer because https://stackoverflow.com/a/25823885/4570472
            start_time = timer()
            inference_alg_concentration_param_results = utils.inference.run_inference_alg(
                inference_alg_str=inference_alg_str,
                observations=sampled_binary_linear_gaussian_results['observations_seq'],
                concentration_param=concentration_param,
                likelihood_model='linear_gaussian',
                learning_rate=1e0)

            # record elapsed time
            stop_time = timer()
            runtime = stop_time - start_time

            # record scores
            scores, pred_cluster_labels = utils.metrics.score_predicted_clusters(
                true_cluster_labels=sampled_binary_linear_gaussian_results['assigned_table_seq'],
                table_assignment_posteriors=inference_alg_concentration_param_results['table_assignment_posteriors'])

            # count number of clusters
            num_clusters = len(np.unique(pred_cluster_labels))

            # write to disk and delete
            data_to_store = dict(
                inference_alg_concentration_param_results=inference_alg_concentration_param_results,
                num_clusters=num_clusters,
                scores=scores,
                runtime=runtime,
            )

            joblib.dump(data_to_store,
                        filename=inference_alg_results_concentration_param_path)
            del inference_alg_concentration_param_results
            del data_to_store

        # read results from disk
        stored_data = joblib.load(
            inference_alg_results_concentration_param_path)

        plot_inference_results(
            sampled_mog_results=sampled_binary_linear_gaussian_results,
            inference_results=stored_data['inference_alg_concentration_param_results'],
            inference_alg_str=inference_alg_str,
            concentration_param=concentration_param,
            plot_dir=inference_alg_plot_dir)

        num_clusters_by_concentration_param[concentration_param] = stored_data[
            'num_clusters']
        scores_by_concentration_param[concentration_param] = stored_data[
            'scores']
        runtimes_by_concentration_param[concentration_param] = stored_data[
            'runtime']

        print('Finished {} concentration_param={:.2f}'.format(inference_alg_str, concentration_param))

    inference_alg_concentration_param_results = dict(
        num_clusters_by_param=num_clusters_by_concentration_param,
        scores_by_param=pd.DataFrame(scores_by_concentration_param).T,
        runtimes_by_param=runtimes_by_concentration_param,
    )

    return inference_alg_concentration_param_results


if __name__ == '__main__':
    main()
