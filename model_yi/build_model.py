import plotly.express as px
import chart_studio.plotly as py
import pandas as pd 
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from catboost import CatBoostClassifier # cb = CatBoostClassifier()
import lightgbm as lgb #
from lightgbm import LGBMClassifier #
import xgboost
from sklearn.ensemble import ExtraTreesClassifier #
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis #
from sklearn.ensemble import GradientBoostingClassifier #
from sklearn.ensemble import AdaBoostClassifier #
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis #
from sklearn.ensemble import (
    RandomForestClassifier,
)
from sklearn.linear_model import RidgeClassifier
from sklearn.svm import (
    SVC,
)
from sklearn.tree import (
    DecisionTreeClassifier,
)
from sklearn.naive_bayes import (
    GaussianNB,
)
from sklearn.neighbors import (
    KNeighborsClassifier,
)
from sklearn.linear_model import (
    LogisticRegression,
)

from sklearn import model_selection

from yellowbrick.classifier import (
    ConfusionMatrix,
    ROCAUC,
    PRCurve,
)
from yellowbrick.model_selection import (
    LearningCurve,
)

# 1. comapare model plot
def compare_model_plot():
    compare_model_df = pd.read_csv("compare_model_df.csv")
    compare_model_df1 = pd.melt(compare_model_df, id_vars=['Model'], var_name='Measurement', value_name='Score')
    fig = px.line(compare_model_df1, x="Measurement", y="Score", color="Model",hover_name="Model",
                title='Measurement score of different models')
    return fig

# 2. roc / prc / cm / lc
X_train = pd.read_csv("data/X_train.csv")
X_test = pd.read_csv("data/X_test.csv")
y_train = pd.read_csv("data/y_train.csv")
y_test = pd.read_csv("data/y_test.csv")

def fit_model(model, X_train_resampled, y_train_resampled, X_test, y_test):
    clf = model()
    kfold = model_selection.KFold(
        n_splits=5,
        shuffle=True
    )
    s = model_selection.cross_val_score(
        clf, X_train_resampled, y_train_resampled, scoring='roc_auc', cv=kfold,
    )
    auc = s.mean()
    std = s.std()
    # roc
    roc_viz = ROCAUC(clf)
    roc_viz.fit(X_train_resampled, y_train_resampled)
    roc_viz.score(X_test, y_test)
    roc_viz.show(outpath = "roc_viz.jpg")
    # prc
    prc_viz = PRCurve(clf)
    prc_viz.fit(X_train_resampled, y_train_resampled)
    prc_viz.score(X_test, y_test)
    prc_viz.show(outpath = "prc_viz.jpg")
    # cm
    cm_viz = ConfusionMatrix(clf, classes=['active', 'not active'])
    cm_viz.fit(X_train_resampled, y_train_resampled)
    cm_viz.score(X_test, y_test)
    cm_viz.show(outpath = "cm_viz.jpg")
    # lc
    lc_viz = LearningCurve(clf)
    lc_viz.fit(X_train_resampled, y_train_resampled)
    lc_viz.score(X_test, y_test)
    lc_viz.show(outpath = "lc_viz.jpg")
    return clf

models_list = [
    DummyClassifier,
    CatBoostClassifier,
    LGBMClassifier,
    xgboost.XGBRFClassifier,
    ExtraTreesClassifier,
    LinearDiscriminantAnalysis,
    GradientBoostingClassifier,
    AdaBoostClassifier,
    QuadraticDiscriminantAnalysis,
    RandomForestClassifier,
    RidgeClassifier,
    SVC,
    DecisionTreeClassifier,
    GaussianNB,
    KNeighborsClassifier,
    LogisticRegression, 
]

# USAGE
clf = fit_model(DummyClassifier, X_train, y_train, X_test, y_test)

# 3. profiling
import pandas_profiling as pp
df_ml_orig = pd.read_csv("data/df_ml_orig.csv")
df_ml_orig = pd.get_dummies(df_ml_orig)
profile = pp.ProfileReport(df_ml_orig)
profile.to_file("data_report.json")
profile.to_file("data_report.html")