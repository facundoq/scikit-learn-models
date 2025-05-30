from pathlib import Path

import numpy as np
import pandas as pd
import sklearn.datasets
import sklearn.tree
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from tqdm import tqdm

from sklearnmodels.scikit.rule_oner import OneRClassifier
from sklearnmodels.scikit.rule_prism import PRISMClassifier
from sklearnmodels.scikit.rule_zeror import ZeroRClassifier
from sklearnmodels.scikit.tree_classification import SKLearnClassificationTree


def read_classification_dataset(path: Path):
    df = pd.read_csv(path)
    x = df.iloc[:, :-1]
    le = LabelEncoder().fit(df.iloc[:, -1])
    y = le.transform(df.iloc[:, -1])
    # y = y.reshape(len(y),1)
    return x, y, le.classes_


def get_zeror_classifier(x: pd.DataFrame, classes: int):
    model = ZeroRClassifier()
    return model


def get_oner_classifier(criterion: str):

    def build(x: pd.DataFrame, classes: int):
        model = OneRClassifier(criterion)
        return model

    return build


def get_prism_classifier(criterion: str):
    def build(x: pd.DataFrame, classes: int):
        n, m = x.shape
        max_length = min(max(int(np.log(m) * 3), 5), 30)
        min_rule_support = max(10, int(n * (0.05 / classes)))
        min_error_decrease = 0.05 / classes
        model = PRISMClassifier(
            criterion=criterion,
            max_rule_length=max_length,
            min_rule_support=min_rule_support,
            error_tolerance=min_error_decrease,
        )

        return model

    return build


def get_nominal_tree_classifier(criterion: str):
    def build_nominal_tree_classifier(x: pd.DataFrame, classes: int):
        n, m = x.shape
        max_height = min(max(int(np.log(m) * 3), 5), 30)
        min_samples_leaf = max(10, int(n * (0.05 / classes)))
        min_samples_split = min_samples_leaf
        min_error_decrease = 0.05 / classes

        return SKLearnClassificationTree(
            criterion=criterion,
            max_depth=max_height,
            min_samples_leaf=min_samples_leaf,
            min_samples_split=min_samples_split,
            min_error_decrease=min_error_decrease,
            splitter=4,
        )

    return build_nominal_tree_classifier


def train_test_classification_model(model_name: str, model_generator, dataset: Path):
    dataset_name = dataset.name.split(".")[0]
    x, y, class_names = read_classification_dataset(dataset)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, train_size=0.8, stratify=y, shuffle=True, random_state=0
    )
    model = model_generator(x_train, len(class_names))
    model.fit(x_train, y_train)

    y_pred_train = model.predict(x_train)
    score_train = accuracy_score(y_train, y_pred_train)
    y_pred_test = model.predict(x_test)
    score_test = accuracy_score(y_test, y_pred_test)
    return {
        "Dataset": dataset_name,
        "Model": model_name,
        "Train": score_train,
        "Test": score_test,
    }


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
    min_samples_leaf = max(10, int(n * (0.05 / classes)))
    min_samples_split = min_samples_leaf
    min_error_improvement = 0.05 / classes
    model = sklearn.tree.DecisionTreeClassifier(
        max_depth=max_height,
        min_samples_leaf=min_samples_leaf,
        min_samples_split=min_samples_split,
        min_impurity_decrease=min_error_improvement,
        criterion="entropy",
        random_state=0,
    )
    return get_sklearn_pipeline(x, model)


path = Path("datasets/classification")
dataset_names = [
    "2_clases_simple.csv",
    "6_clases_dificil.csv",
    "diabetes.csv",
    "ecoli.csv",
    "golf_classification_nominal.csv",
    "golf_classification_numeric.csv",
    "seeds.csv",
    "sonar.csv",
    "titanic.csv",
]


def check_results(
    at_least_percent: float, results: dict[str, dict[str, float]], reference_model: str
):
    results = results.copy()
    reference = results.pop(reference_model)

    for model_name, model_results in results.items():

        for set in ["Train", "Test"]:
            reference_score = reference[set]
            model_score = model_results[set]
            percent = model_score / reference_score
            alp = at_least_percent[model_name]
            assert (
                alp <= percent
            ), f"{set} accuracy of {model_name} ({model_score:.2g}) should be at least {alp*100:.2g}% of {reference_model} ({reference_score:.2g}) on dataset {reference["Dataset"]}, was only {percent*100:.2g}%."  # noqa: E501


def test_performance_similar_sklearn(at_least_percent=0.8, dataset_names=dataset_names):
    models = {
        "sklearn.tree": get_sklearn_tree,
        "tree[entropy]": get_nominal_tree_classifier("entropy"),
        "tree[gini]": get_nominal_tree_classifier("gini"),
        "tree[gain_ratio]": get_nominal_tree_classifier("gain_ratio"),
        "zeror": get_zeror_classifier,
        "oner[entropy]": get_oner_classifier("entropy"),
        "oner[gain_ratio]": get_oner_classifier("gain_ratio"),
    }
    at_least_percent = {
        "tree[entropy]": 0.8,
        "tree[gini]": 0.8,
        "tree[gain_ratio]": 0.8,
        "zeror": 0.1,
        "oner[entropy]": 0.2,
        "oner[gain_ratio]": 0.2,
    }
    datasets = [path / name for name in dataset_names]
    results_all = []
    for dataset in tqdm(datasets, desc="Datasets"):
        results = {
            k: train_test_classification_model(k, m, dataset) for k, m in models.items()
        }
        check_results(at_least_percent, results, "sklearn.tree")
        results_all += list(results.values())

    print(pd.DataFrame.from_records(results_all))


if __name__ == "__main__":
    test_performance_similar_sklearn()
