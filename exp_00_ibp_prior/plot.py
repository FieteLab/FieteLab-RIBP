import matplotlib
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.stats
import seaborn as sns


alphas_color_map = {
    1.1: 'tab:blue',
    10.37: 'tab:orange',
    15.78: 'tab:purple',
    30.91: 'tab:green'
}


def plot_analytics_vs_monte_carlo_customer_dishes(sampled_customers_dishes_by_alpha_beta,
                                                  analytical_customers_dishes_by_alpha_beta,
                                                  plot_dir):
    # plot analytics versus monte carlo estimates
    for alpha_and_beta in sampled_customers_dishes_by_alpha_beta.keys():
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))

        sampled_customer_tables = sampled_customers_dishes_by_alpha_beta[alpha_and_beta]
        average_customer_tables = np.mean(sampled_customer_tables, axis=0)
        analytical_customer_dishes = analytical_customers_dishes_by_alpha_beta[alpha_and_beta]

        max_sampled_table = np.argmax(np.sum(average_customer_tables, axis=0) == 0)

        # replace 0s with nans to allow for log scaling
        average_customer_tables[average_customer_tables == 0.] = np.nan
        cutoff = np.nanmin(average_customer_tables)
        analytical_customer_dishes[analytical_customer_dishes < cutoff] = np.nan

        ax = axes[0]
        sns.heatmap(average_customer_tables[:, :max_sampled_table],
                    ax=ax,
                    mask=np.isnan(average_customer_tables)[:, :max_sampled_table],
                    cmap='jet',
                    vmin=cutoff,
                    vmax=1.,
                    norm=LogNorm(),
                    # cbar_kws=dict(label='$p(z_{tk}=1)$'),
                    )

        ax.set_title(r'Monte Carlo  $p(z_{tk} = 1 | $' + alpha_and_beta + ')')
        ax.set_ylabel(r'Customer Index')
        ax.set_xlabel(r'Dish Index')

        ax = axes[1]
        sns.heatmap(analytical_customer_dishes[:, :max_sampled_table],
                    ax=ax,
                    mask=np.isnan(analytical_customer_dishes)[:, :max_sampled_table],
                    cmap='jet',
                    vmin=cutoff,
                    vmax=1.,
                    norm=LogNorm(),
                    )
        ax.set_title(r'Analytical  $p(z_{tk} = 1 | $' + alpha_and_beta + ')')
        ax.set_xlabel(r'Dish Index')

        alpha_and_beta = alpha_and_beta.split('=')
        alpha = alpha_and_beta[1].split(',')[0]
        beta = alpha_and_beta[2][:-1]
        fig.savefig(os.path.join(plot_dir, f'analytics_vs_monte_carlo_customer_tables_a={alpha}_b={beta}.png'),
                    bbox_inches='tight',
                    dpi=300)
        # plt.show()
        plt.close()


def plot_analytical_vs_monte_carlo_mse(error_means_per_num_samples_per_alpha,
                                       error_sems_per_num_samples_per_alpha,
                                       num_reps,
                                       plot_dir):

    alphas_and_betas = list(error_sems_per_num_samples_per_alpha.keys())

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(5, 4))
    for alpha_beta in alphas_and_betas:
        ax.errorbar(x=list(error_means_per_num_samples_per_alpha[alpha_beta].keys()),
                    y=list(error_means_per_num_samples_per_alpha[alpha_beta].values()),
                    yerr=list(error_sems_per_num_samples_per_alpha[alpha_beta].values()),
                    label=alpha_beta,
                    )
    ax.legend(title=f'Num Repeats: {num_reps}')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_ylabel(r'(Analytic - Monte Carlo$)^2$')
    # ax.set_ylabel(r'$\mathbb{E}_D[\sum_k (\mathbb{E}[N_{T, k}] - \frac{1}{S} \sum_{s=1}^S N_{T, k}^{(s)})^2]$')
    ax.set_xlabel('Number of Monte Carlo Samples')
    fig.savefig(os.path.join(plot_dir, f'ibp_analytical_vs_monte_carlo_mse.png'),
                bbox_inches='tight',
                dpi=300)
    # plt.show()
    plt.close()


def plot_indian_buffet_num_dishes_dist_by_customer_num(analytical_dish_distribution_poisson_rate_by_alpha_by_T,
                                                       plot_dir):
    # plot how the CRT table distribution changes for T customers
    alphas_and_betas = list(analytical_dish_distribution_poisson_rate_by_alpha_by_T.keys())
    T = len(analytical_dish_distribution_poisson_rate_by_alpha_by_T[alphas_and_betas[0]])
    customer_idx = 1 + np.arange(T)
    cmap = plt.get_cmap('jet_r')

    for alpha_and_beta in alphas_and_betas:
        for t in customer_idx:
            max_val = 2 * analytical_dish_distribution_poisson_rate_by_alpha_by_T[alpha_and_beta][T]
            x = np.arange(0, max_val)
            y = scipy.stats.poisson.pmf(x, mu=analytical_dish_distribution_poisson_rate_by_alpha_by_T[alpha_and_beta][t])
            plt.plot(x,
                     y,
                     # label=f'T={t}',
                     color=cmap(float(t) / T))

        # https://stackoverflow.com/questions/43805821/matplotlib-add-colorbar-to-non-mappable-object
        norm = matplotlib.colors.Normalize(vmin=1, vmax=T)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        colorbar = plt.colorbar(sm,
                                ticks=np.arange(1, T + 1, 5),
                                # boundaries=np.arange(-0.05, T + 0.1, .1)
                                )
        colorbar.set_label('Number of Customers')
        plt.title(fr'Indian Buffet Dish Distribution ({alpha_and_beta})')
        plt.xlabel(r'Number of Dishes after T Customers')
        plt.ylabel(r'P(Number of Dishes after T Customers)')
        plt.xlim(0., max_val)

        alpha_and_beta = alpha_and_beta.split('=')
        alpha = alpha_and_beta[1].split(',')[0]
        beta = alpha_and_beta[2][:-1]

        plt.savefig(os.path.join(plot_dir, f'ibp_dish_distribution_a={alpha}_b={beta}.png'),
                    bbox_inches='tight',
                    dpi=300)
        # plt.show()
        plt.close()


def plot_recursion_visualization(analytical_customers_dishes_by_alpha_beta,
                                 analytical_dish_distribution_poisson_rate_by_alpha_by_T,
                                 plot_dir):
    alphas_and_betas = list(analytical_customers_dishes_by_alpha_beta.keys())
    cutoff = 1e-8

    for alpha_and_beta in alphas_and_betas:
        fig, axes = plt.subplots(nrows=1,
                                 ncols=5,
                                 figsize=(13, 4),
                                 gridspec_kw={"width_ratios": [1, 0.1, 1, 0.1, 1]},
                                 sharex=True)

        ax = axes[0]
        cum_customer_dish_eating_probs = np.cumsum(analytical_customers_dishes_by_alpha_beta[alpha_and_beta], axis=0)
        cum_customer_dish_eating_probs[cum_customer_dish_eating_probs < cutoff] = np.nan

        # figure out which dish falls below cutoff. if no dishes are below threshold, need to set
        max_dish_idx = np.argmax(np.nansum(cum_customer_dish_eating_probs, axis=0) < cutoff)
        if max_dish_idx == 0 and np.nansum(cum_customer_dish_eating_probs, axis=0)[max_dish_idx] >= cutoff:
            max_dish_idx = cum_customer_dish_eating_probs.shape[1]
        sns.heatmap(
            data=cum_customer_dish_eating_probs[:, :max_dish_idx],
            ax=ax,
            cbar_kws=dict(label=r'$\sum_{t^{\prime} = 1}^{t-1} p(z_{t^{\prime} k} = 1)$'),
            cmap='jet',
            mask=np.isnan(cum_customer_dish_eating_probs[:, :max_dish_idx]),
            vmin=cutoff,
            norm=LogNorm(),
        )
        ax.set_xlabel('Dish Index')
        ax.set_ylabel('Customer Index')
        ax.set_title('Running Sum of\nPrev. Customers\' Distributions')

        # necessary to make space for colorbar text
        axes[1].axis('off')

        ax = axes[2]
        table_distributions_by_T_array = np.stack([
            scipy.stats.poisson.pmf(np.arange(max_dish_idx),
                                    mu=analytical_dish_distribution_poisson_rate_by_alpha_by_T[alpha_and_beta][key])
            for key in sorted(analytical_dish_distribution_poisson_rate_by_alpha_by_T[alpha_and_beta].keys())])
        table_distributions_by_T_array[table_distributions_by_T_array < cutoff] = np.nan
        sns.heatmap(
            data=table_distributions_by_T_array[:, :max_dish_idx],
            ax=ax,
            cbar_kws=dict(label=r'$p(\Lambda_t = \ell)$'),
            cmap='jet',
            mask=np.isnan(table_distributions_by_T_array[:, :max_dish_idx]),
            vmin=cutoff,
            norm=LogNorm(),
        )
        ax.set_title('Distribution over\nNumber of Dishes')
        ax.set_xlabel('Dish Index')

        # necessary to make space for colorbar text
        axes[3].axis('off')

        ax = axes[4]
        analytical_customer_dishes = np.copy(analytical_customers_dishes_by_alpha_beta[alpha_and_beta])
        analytical_customer_dishes[analytical_customer_dishes < cutoff] = np.nan
        sns.heatmap(
            data=analytical_customer_dishes[:, :max_dish_idx],
            ax=ax,
            cbar_kws=dict(label='$p(z_{tk}=1)$'),
            cmap='jet',
            mask=np.isnan(analytical_customer_dishes[:, :max_dish_idx]),
            norm=LogNorm(vmin=cutoff, ),
        )
        ax.set_title('New Customer\'s Distribution')
        ax.set_xlabel('Dish Index')

        alpha_and_beta = alpha_and_beta.split('=')
        alpha = alpha_and_beta[1].split(',')[0]
        beta = alpha_and_beta[2][:-1]
        fig.savefig(os.path.join(plot_dir, f'ibp_recursion_a={alpha}_b={beta}.png'),
                    bbox_inches='tight',
                    dpi=300)
        # plt.show()
        plt.close()
