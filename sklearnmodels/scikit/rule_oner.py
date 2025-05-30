from sklearnmodels.backend.factory import DEFAULT_BACKEND
from sklearnmodels.rules.oner import OneR
from sklearnmodels.scikit.nominal_model import NominalClassifier


import numpy as np
import pandas as pd


class OneRClassifier(NominalClassifier):
    def __init__(self, criterion="entropy", backend=DEFAULT_BACKEND, class_weight=None):
        super().__init__(backend=backend, class_weight=class_weight)
        self.criterion = criterion

    def fit(self, x: pd.DataFrame, y: np.ndarray):
        d = self.validate_data_fit_classification(x, y)
        error = self.build_error(self.criterion, len(self.classes_))
        trainer = OneR(error_function=error)
        model = trainer.fit(d)
        self.set_model(model)
        return self
