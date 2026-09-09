def roc_auc_manual(valores_reais, scores):
    ordem = np.argsort(scores)
    ranks = np.empty_like(ordem, dtype=float)
    ranks[ordem] = np.arange(1, len(scores) + 1)
    positivos = valores_reais == 1
    negativos = ~positivos
    quantidade_positivos = positivos.sum()
    quantidade_negativos = negativos.sum()
    soma_ranks_positivos = ranks[positivos].sum()
    return (
        soma_ranks_positivos
        - quantidade_positivos * (quantidade_positivos + 1) / 2
    ) / (quantidade_positivos * quantidade_negativos)


def folds_estratificados(valores_reais, quantidade_folds=3, seed=42):
    gerador = np.random.default_rng(seed)
    indices_positivos = gerador.permutation(np.flatnonzero(valores_reais == 1))
    indices_negativos = gerador.permutation(np.flatnonzero(valores_reais == 0))
    folds_positivos = np.array_split(indices_positivos, quantidade_folds)
    folds_negativos = np.array_split(indices_negativos, quantidade_folds)

    for indice_fold in range(quantidade_folds):
        indices_validacao = np.concatenate(
            [folds_positivos[indice_fold], folds_negativos[indice_fold]]
        )
        indices_treino = np.setdiff1d(
            np.arange(len(valores_reais)), indices_validacao
        )
        yield indices_treino, indices_validacao


def objetivo(trial):
    parametros = {
        'objective': 'binary',
        'verbosity': -1,
        'seed': 42,
        'feature_fraction_seed': 42,
        'bagging_seed': 42,
        'num_threads': 1,
        'force_col_wise': True,
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 4, 24),
        'max_depth': trial.suggest_int('max_depth', 2, 6),
        'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 10, 50),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.7, 1.0),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.7, 1.0),
        'lambda_l1': trial.suggest_float('lambda_l1', 0.0, 2.0),
        'lambda_l2': trial.suggest_float('lambda_l2', 0.0, 2.0),
    }
    quantidade_boosting = trial.suggest_int('num_boost_round', 50, 250)
    resultados = []

    for indices_treino, indices_validacao in folds_estratificados(y_treino):
        dados_treino = lgb.Dataset(
            X_treino[indices_treino],
            label=y_treino[indices_treino],
            feature_name=features,
        )
        dados_validacao = lgb.Dataset(
            X_treino[indices_validacao],
            label=y_treino[indices_validacao],
            feature_name=features,
            reference=dados_treino,
        )
        modelo = lgb.train(
            parametros,
            dados_treino,
            num_boost_round=quantidade_boosting,
            valid_sets=[dados_validacao],
            callbacks=[lgb.early_stopping(30, verbose=False)],
        )
        previsoes = modelo.predict(X_treino[indices_validacao])
        resultados.append(roc_auc_manual(y_treino[indices_validacao], previsoes))

    return np.mean(resultados)