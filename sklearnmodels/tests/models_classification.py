import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import sklearn.tree
from sklearnmodels.scikit.naive_bayes import NaiveBayesClassifier
from sklearnmodels.scikit.nominal_model import NominalModel
from sklearnmodels.scikit.rule_cn2 import CN2Classifier
from sklearnmodels.scikit.rule_oner import OneRClassifier


import pandas as pd

from sklearnmodels.scikit.rule_prism import PRISMClassifier
from sklearnmodels.scikit.rule_zeror import ZeroRClassifier
from sklearnmodels.scikit.tree_classification import TreeClassifier


def get_oner_classifier(criterion: str):

    def build(x: pd.DataFrame, classes: int):
        model = OneRClassifier(criterion)
        return model

    return build


def get_naive_bayes(smoothing: float):

    def build(x: pd.DataFrame, classes: int):
        model = NaiveBayesClassifier(smoothing=smoothing)
        return model

    return build


def get_nominal_tree_classifier(criterion: str):
    def build_nominal_tree_classifier(x: pd.DataFrame, classes: int):
        n, m = x.shape
        max_height = min(max(int(np.log(m) * 3), 5), 30)
        min_samples_leaf = max(2, int(n * (0.05 / classes)))
        min_samples_split = min_samples_leaf
        min_error_decrease = 0.01 / classes

        return TreeClassifier(
            criterion=criterion,
            max_depth=max_height,
            min_samples_leaf=min_samples_leaf,
            min_samples_split=min_samples_split,
            min_error_decrease=min_error_decrease,
            splitter=4,
        )

    return build_nominal_tree_classifier


def get_prism_classifier():
    def build(x: pd.DataFrame, classes: int):
        n, m = x.shape
        max_length = min(max(int(np.log(m) * 3), 5), 30)
        min_rule_support = max(2, int(n * (0.05 / classes)))
        min_error_decrease = 0.05 / classes
        model = PRISMClassifier(
            max_rule_length=max_length,
            min_rule_support=min_rule_support,
            max_error_per_rule=min_error_decrease,
        )

        return model

    return build


def get_cn2_classifier(criterion: str):
    def build(x: pd.DataFrame, classes: int):
        n, m = x.shape
        max_length = min(max(int(np.log(m) * 3), 5), 30)
        min_rule_support = max(2, int(n * (0.05 / classes)))
        max_error_per_rule = 0.5 / classes
        model = CN2Classifier(
            criterion=criterion,
            max_rule_length=max_length,
            min_rule_support=min_rule_support,
            max_error_per_rule=max_error_per_rule,
        )

        return model

    return build


def get_sklearn_pipeline(x: pd.DataFrame, model):
    numeric_features = x.select_dtypes(include=["int64", "float64"]).columns
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_features = x.select_dtypes(exclude=["int64", "float64"]).columns
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", model)])


def get_sklearn_tree(x: pd.DataFrame, classes: int):
    n, m = x.shape
    max_height = min(max(int(np.log(m) * 3), 5), 30)
    min_samples_leaf = max(2, int(n * (0.05 / classes)))
    min_samples_split = min_samples_leaf
    min_error_improvement = 0.01 / classes
    model = sklearn.tree.DecisionTreeClassifier(
        max_depth=max_height,
        min_samples_leaf=min_samples_leaf,
        min_samples_split=min_samples_split,
        min_impurity_decrease=min_error_improvement,
        criterion="entropy",
        random_state=0,
    )
    return get_sklearn_pipeline(x, model)


def get_zeror_classifier(x: pd.DataFrame, classes: int):
    model = ZeroRClassifier()
    return model
