import abc
import numpy as np
import pandas as pd

class TargetError(abc.ABC):

    @abc.abstractmethod
    def __call__(self,y:np.ndarray)->float:
        pass
    
    @abc.abstractmethod
    def prediction(self,y:np.ndarray):
        pass
    
    def __repr__(self):
        return self.__class__.__name__
    
eps = 1e-32
def log(x,base):
    x[x<eps]=eps
    if base==2:
        return np.log2(x)
    elif base == 0:
        return np.log(x)
    elif base == 10:
        return np.log10(x)
    else:
        lb = 1/np.log(base)
        return np.log(x) * lb

class ClassificationError(TargetError):
    def __init__(self,classes:int):
        self.classes=classes
    def prediction(self,y:np.ndarray):
        if len(y)==0:
            return np.ones(self.classes)/self.classes
        else:
            if np.issubdtype(y.dtype,object):
                #string classes
                y_cat = pd.Series(data=y.squeeze()).astype("category")
                y = y_cat.cat.codes.to_numpy().reshape(-1,1)
            #numeric index classes classes
            counts = np.bincount(y[:,0],minlength=self.classes)
            return counts/counts.sum()
    def __repr__(self):
            return f"{super().__repr__()}(classes={self.classes})"


class EntropyMetric(ClassificationError):
    def __init__(self,classes:int,base=2):
        super().__init__(classes)
        self.base=base
    def __call__(self, y:np.ndarray):
        p = self.prediction(y)
        # largest_value = log(np.array([self.classes]),self.base)[0]
        return -np.sum(p*log(p,self.classes))
    
class RegressionMetric(TargetError):
    def prediction(self,y:np.ndarray):
        return np.mean(y,axis=0)

class DeviationMetric(RegressionMetric):
    def __call__(self, y:np.ndarray):
        if y.shape[0]==0:
            return np.inf
        return np.sum(np.std(y,axis=0))