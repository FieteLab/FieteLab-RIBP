import numpy as np
import os
import pandas as pd
import sklearn
import torch
import torchvision


def load_moseq_dataset(data_dir: str = 'data'):
    """
    Load MoSeq data from https://github.com/dattalab/moseq-drugs.

    Note: You need to download the data from https://doi.org/10.5281/zenodo.3951698.
    Unfortunately, the data appears to have been pickled using Python2.7 and now
    NumPy and joblib can't read it. I used Python2.7 and Joblib to dump the data
    to disk using the following code:


    moseq_dir = os.path.join('data/moseq_drugs')
    file_names = [
        'dataset',
        'fingerprints',
        'syllablelabels'
    ]
    data = dict()
    for file_name in file_names:
        data[file_name] = np.load(os.path.join(moseq_dir, file_name + '.pkl'),
                                  allow_pickle=True)
    joblib.dump(value=data,
                filename=os.path.join(moseq_dir, 'moseq_drugs_data.joblib'))
    """

    moseq_dir = os.path.join(data_dir, 'moseq_drugs')
    data = joblib.load(filename=os.path.join(moseq_dir, 'moseq_drugs_data.joblib'))
    dataset = data['dataset']
    fingerprints = data['fingerprints']
    syllablelabels = data['syllablelabels']

    moseq_dataset_results = dict(
        dataset=dataset,
        fingerprints=fingerprints,
        syllablelabels=syllablelabels)

    return moseq_dataset_results


def load_newsgroup_dataset(data_dir: str = 'data',
                           num_data: int = None,
                           num_features: int = 500,
                           tf_or_tfidf_or_counts: str = 'tfidf'):
    assert tf_or_tfidf_or_counts in {'tf', 'tfidf', 'counts'}

    # categories = ['soc.religion.christian', 'comp.graphics', 'sci.med']
    categories = None  # set to None for all categories

    twenty_train = sklearn.datasets.fetch_20newsgroups(
        data_home=data_dir,
        subset='train',  # can switch to 'test'
        categories=categories,
        shuffle=True,
        random_state=0)

    class_names = np.array(twenty_train.target_names)
    true_cluster_labels = twenty_train.target
    true_cluster_label_strs = class_names[true_cluster_labels]
    observations = twenty_train.data

    if num_data is None:
        num_data = len(class_names)
    observations = observations[:num_data]
    true_cluster_labels = true_cluster_labels[:num_data]
    true_cluster_label_strs = true_cluster_label_strs[:num_data]

    if tf_or_tfidf_or_counts == 'tf':
        feature_extractor = sklearn.feature_extraction.text.TfidfVectorizer(
            max_features=num_features,  # Lin 2013 used 5000
            sublinear_tf=False,
            use_idf=False,
        )
        observations_transformed = feature_extractor.fit_transform(observations)

    elif tf_or_tfidf_or_counts == 'tfidf':
        # convert documents' word counts to tf-idf (Term Frequency times Inverse Document Frequency)
        # equivalent to CountVectorizer() + TfidfTransformer()
        # for more info, see
        # https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html
        # https://scikit-learn.org/stable/auto_examples/text/plot_document_clustering.html#sphx-glr-auto-examples-text-plot-document-clustering-py
        feature_extractor = sklearn.feature_extraction.text.TfidfVectorizer(
            max_features=num_features,  # Lin 2013 used 5000
            sublinear_tf=False,
            use_idf=True,
        )
        observations_transformed = feature_extractor.fit_transform(observations)
    elif tf_or_tfidf_or_counts == 'counts':
        feature_extractor = sklearn.feature_extraction.text.CountVectorizer(
            max_features=num_features)
        observations_transformed = feature_extractor.fit_transform(observations)
    else:
        raise ValueError

    # quoting from Lin NeurIPS 2013:
    # We pruned the vocabulary to 5000 words by removing stop words and
    # those with low TF-IDF scores, and obtained 150 topics by running LDA [3]
    # on a subset of 20K documents. We held out 10K documents for testing and use the
    # remaining to train the DPMM. We compared SVA,SVA-PM, and TVF.

    # possible likelihoods for TF-IDF data
    # https://stats.stackexchange.com/questions/271923/how-to-use-tfidf-vectors-with-multinomial-naive-bayes
    # https://stackoverflow.com/questions/43237286/how-can-we-use-tfidf-vectors-with-multinomial-naive-bayes
    newsgroup_dataset_results = dict(
        observations_transformed=observations_transformed.toarray(),  # remove .toarray() to keep CSR matrix
        true_cluster_label_strs=true_cluster_label_strs,
        assigned_table_seq=true_cluster_labels,
        feature_extractor=feature_extractor,
        feature_names=feature_extractor.get_feature_names(),
    )

    return newsgroup_dataset_results


def load_mnist_dataset(data_dir: str = 'data',
                       num_data: int = None,
                       center_crop: bool = False,
                       avg_pool: bool = False,
                       feature_extractor_method: str = 'pca'):

    assert feature_extractor_method in {'pca', 'none'}
    transforms = [torchvision.transforms.ToTensor()]
    if center_crop:
        transforms.append(torchvision.transforms.CenterCrop((80, 80)))
    if avg_pool:
        transforms.append(torchvision.transforms.Lambda(
            lambda x: torch.nn.functional.avg_pool2d(x, kernel_size=9, stride=3)))
        raise NotImplementedError

    mnist_dataset = torchvision.datasets.MNIST(
        root=data_dir,
        download=True,
        transform=torchvision.transforms.Compose(transforms))

    if num_data is None:
        num_data = mnist_dataset.data.shape[0]
    indices = np.random.choice(np.arange(mnist_dataset.data.shape[0]),
                               size=num_data,
                               replace=False)
    observations = mnist_dataset.data[indices, :, :].numpy()
    labels = mnist_dataset.targets[indices].numpy()

    if feature_extractor_method == 'pca':
        from sklearn.decomposition import PCA
        image_height = mnist_dataset.data.shape[1]
        image_width = mnist_dataset.data.shape[2]
        reshaped_images = np.reshape(observations, newshape=(num_data, image_height * image_width))
        pca = PCA(n_components=50)
        pca_latents = pca.fit_transform(reshaped_images)
        image_features = np.reshape(pca.inverse_transform(pca_latents),
                                    newshape=(num_data, image_height, image_width))
        feature_extractor = pca
    else:
        raise ValueError(f'Impermissible feature method: {feature_extractor_method}')

    # # visualize observations if curious
    # import matplotlib.pyplot as plt
    # for idx in range(10):
    #     plt.imshow(image_features[idx], cmap='gray')
    #     plt.show()

    mnist_dataset_results = dict(
        observations=observations,
        labels=labels,
        feature_extractor_method=feature_extractor_method,
        feature_extractor=feature_extractor,
        image_features=image_features,
    )

    return mnist_dataset_results


def load_omniglot_dataset(data_dir: str = 'data',
                          num_data: int = None,
                          center_crop: bool = True,
                          avg_pool: bool = False,
                          feature_extractor_method: str = 'pca'):
    """

    """

    assert feature_extractor_method in {'pca', 'cnn', 'vae', 'vae_old'}

    # https://pytorch.org/tutorials/beginner/basics/data_tutorial.html
    transforms = [torchvision.transforms.ToTensor()]
    if center_crop:
        transforms.append(torchvision.transforms.CenterCrop((80, 80)))
    if avg_pool:
        transforms.append(torchvision.transforms.Lambda(
            lambda x: torch.nn.functional.avg_pool2d(x, kernel_size=9, stride=3)))

    omniglot_dataset = torchvision.datasets.Omniglot(
        root=data_dir,
        download=True,
        transform=torchvision.transforms.Compose(transforms))

    # truncate dataset for now
    # character_classes = [images_and_classes[1] for images_and_classes in
    #                      omniglot_dataset._flat_character_images]
    if num_data is None:
        num_data = len(omniglot_dataset._flat_character_images)
    omniglot_dataset._flat_character_images = omniglot_dataset._flat_character_images[:num_data]
    dataset_size = len(omniglot_dataset._flat_character_images)

    omniglot_dataloader = torch.utils.data.DataLoader(
        dataset=omniglot_dataset,
        batch_size=1,
        shuffle=False)

    images, labels = [], []
    for image, label in omniglot_dataloader:
        labels.append(label)
        images.append(image[0, 0, :, :])
        # uncomment to deterministically append the first image
        # images.append(omniglot_dataset[0][0][0, :, :])
    images = torch.stack(images).numpy()

    # these might be swapped but I think height = width for omniglot
    _, image_height, image_width = images.shape
    labels = np.array(labels)

    if feature_extractor_method == 'pca':
        from sklearn.decomposition import PCA
        reshaped_images = np.reshape(images, newshape=(dataset_size, image_height * image_width))
        pca = PCA(n_components=20)
        pca_latents = pca.fit_transform(reshaped_images)
        image_features = np.reshape(pca.inverse_transform(pca_latents),
                                    newshape=(dataset_size, image_height, image_width))
        feature_extractor = pca
    elif feature_extractor_method == 'cnn':
        # # for some reason, omniglot uses 1 for background and 0 for stroke
        # # whereas MNIST uses 0 for background and 1 for stroke
        # # for consistency, we'll invert omniglot
        # images = 1. - images
        #
        # from utils.omniglot_feature_extraction import cnn_load
        # lenet = cnn_load()
        #
        # from skimage.transform import resize
        # downsized_images = np.stack([resize(image, output_shape=(28, 28))
        #                              for image in images])
        #
        # # import matplotlib.pyplot as plt
        # # plt.imshow(downsized_images[0], cmap='gray')
        # # plt.title('Test Downsized Omniglot')
        # # plt.show()
        #
        # # add channel dimension for CNN
        # reshaped_images = np.expand_dims(downsized_images, axis=1)
        #
        # # make sure dropout is turned off
        # lenet.eval()
        # image_features = lenet(torch.from_numpy(reshaped_images)).detach().numpy()
        #
        # feature_extractor = lenet

        raise NotImplementedError
    elif feature_extractor_method == 'vae':
        vae_data = np.load('data/omniglot_vae/omniglot_data.npz')
        labels = vae_data['targets']
        indices_to_sort_labels = np.argsort(labels)
        # sort and truncate
        labels = labels[indices_to_sort_labels][:num_data]
        images = vae_data['images'][indices_to_sort_labels][:num_data, :, :]
        image_features = vae_data['latents'][indices_to_sort_labels][:num_data, :]
        feature_extractor = None
    else:
        raise ValueError(f'Impermissible feature method: {feature_extractor_method}')

    # # visualize images if curious
    # import matplotlib.pyplot as plt
    # for idx in range(10):
    #     plt.imshow(image_features[idx], cmap='gray')
    #     plt.show()

    omniglot_dataset_results = dict(
        images=images,
        assigned_table_seq=labels,
        feature_extractor_method=feature_extractor_method,
        feature_extractor=feature_extractor,
        image_features=image_features,
    )

    return omniglot_dataset_results


def load_reddit_dataset(num_data: int,
                        num_features: int,
                        tf_or_tfidf_or_counts='tfidf',
                        data_dir='data'):
    # TODO: rewrite this function to preprocess data similar to newsgroup
    os.makedirs(data_dir, exist_ok=True)

    # possible other alternative datasets:
    #   https://www.tensorflow.org/datasets/catalog/cnn_dailymail
    #   https://www.tensorflow.org/datasets/catalog/newsroom (also in sklearn)

    # useful overview: https://www.tensorflow.org/datasets/overview
    # take only subset of data for speed: https://www.tensorflow.org/datasets/splits
    # specific dataset: https://www.tensorflow.org/datasets/catalog/reddit
    reddit_dataset, reddit_dataset_info = tfds.load(
        'reddit',
        split='train',  # [:1%]',
        shuffle_files=False,
        download=True,
        with_info=True,
        data_dir=data_dir)
    assert isinstance(reddit_dataset, tf.data.Dataset)
    # reddit_dataframe = pd.DataFrame(reddit_dataset.take(10))
    reddit_dataframe = tfds.as_dataframe(
        ds=reddit_dataset.take(num_data),
        ds_info=reddit_dataset_info)
    reddit_dataframe = pd.DataFrame(reddit_dataframe)

    true_cluster_label_strs = reddit_dataframe['subreddit'].values
    true_cluster_labels = reddit_dataframe['subreddit'].astype('category').cat.codes.values

    documents_text = reddit_dataframe['normalizedBody'].values

    # convert documents' word counts to tf-idf (Term Frequency times Inverse Document Frequency)
    # equivalent to CountVectorizer() + TfidfTransformer()
    # for more info, see
    # https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html
    # https://scikit-learn.org/stable/auto_examples/text/plot_document_clustering.html#sphx-glr-auto-examples-text-plot-document-clustering-py
    tfidf_vectorizer = sklearn.feature_extraction.text.TfidfVectorizer(
        max_features=5000,
        sublinear_tf=False)
    observations_transformed = tfidf_vectorizer.fit_transform(documents_text)

    # quoting from Lin NeurIPS 2013:
    # We pruned the vocabulary to 5000 words by removing stop words and
    # those with low TF-IDF scores, and obtained 150 topics by running LDA [3]
    # on a subset of 20K documents. We held out 10K documents for testing and use the
    # remaining to train the DPMM. We compared SVA,SVA-PM, and TVF.

    # possible likelihoods for TF-IDF data
    # https://stats.stackexchange.com/questions/271923/how-to-use-tfidf-vectors-with-multinomial-naive-bayes
    # https://stackoverflow.com/questions/43237286/how-can-we-use-tfidf-vectors-with-multinomial-naive-bayes
    reddit_dataset_results = dict(
        observations_transformed=observations_transformed.toarray(),  # remove .toarray() to keep CSR matrix
        true_cluster_label_strs=true_cluster_label_strs,
        assigned_table_seq=true_cluster_labels,
        tfidf_vectorizer=tfidf_vectorizer,
        feature_names=tfidf_vectorizer.get_feature_names(),
    )

    return reddit_dataset_results


def load_yale_dataset(num_data: int,
                      data_dir='data'):
    npzfile = np.load(os.path.join('data', 'yale_faces', 'yale_faces.npz'))
    data = dict(npzfile)
    train_data = data['train_data']
    test_data = data['test_data']
    # authors suggest withholding pixels from testing set with 0.3% probability
    # these are those pixels
    test_mask = data['test_mask']

    # image size is 32x32. Reshape or no?

    yale_dataset_results = dict(
        train_data=train_data,
        test_data=test_data,
        test_mask=test_mask)

    return yale_dataset_results