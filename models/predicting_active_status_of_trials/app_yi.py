import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    AdaBoostClassifier,
)
from sklearn.dummy import DummyClassifier
from sklearn.discriminant_analysis import (
    LinearDiscriminantAnalysis,
    QuadraticDiscriminantAnalysis)
from sklearn.linear_model import RidgeClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBRFClassifier
from sklearn.metrics import roc_curve, auc, precision_recall_curve, confusion_matrix
from sklearn import model_selection
import sys
sys.path.append('../')


def app():
    st.title('Activeness classification')
    st.write('We use several different classifiers to classify the active status of trials.')

    X_train = pd.read_csv("X_train.csv")
    X_test = pd.read_csv("X_test.csv")
    y_train = pd.read_csv("y_train.csv")
    y_test = pd.read_csv("y_test.csv")

    compare_model_df = pd.read_csv("compare_model_df.csv")

    with st.beta_container():
        st.subheader("Classifiers comparison")
        select_measure = st.selectbox("Please select a metric:",
                                      options=["Accuracy", "AUC", "Recall", "Precision",
                                               "F1", "Kappa", "MCC", "TT (Sec)"])
        fig = px.line(compare_model_df, x="Model", y=select_measure,
                      template="plotly_white",
                      title=f'Compare all models\' {select_measure}')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Choose a classifier")
    select_model = st.selectbox("Please select a  classifier:",
                                options=["RandomForestClassifier",
                                         "LogisticRegression",
                                         "LGBMClassifier",
                                         "XGBRFClassifier",
                                         "LinearDiscriminantAnalysis",
                                         "GradientBoostingClassifier",
                                         "AdaBoostClassifier",
                                         "QuadraticDiscriminantAnalysis",
                                         "RidgeClassifier",
                                         "SVC",
                                         "DecisionTreeClassifier",
                                         "GaussianNB",
                                         "KNeighborsClassifier",
                                         "ExtraTreesClassifier",
                                         "CatBoostClassifier",
                                         "DummyClassifier"])

    models = {"RandomForestClassifier": RandomForestClassifier, "ExtraTreesClassifier": ExtraTreesClassifier,
              "DummyClassifier": DummyClassifier,
              "CatBoostClassifier": CatBoostClassifier, "LGBMClassifier": LGBMClassifier,
              "XGBRFClassifier": XGBRFClassifier,
              "LinearDiscriminantAnalysis": LinearDiscriminantAnalysis,
              "GradientBoostingClassifier": GradientBoostingClassifier,
              "AdaBoostClassifier": AdaBoostClassifier, "QuadraticDiscriminantAnalysis": QuadraticDiscriminantAnalysis,
              "RidgeClassifier": RidgeClassifier, "SVC": SVC, "DecisionTreeClassifier": DecisionTreeClassifier,
              "GaussianNB": GaussianNB, "KNeighborsClassifier": KNeighborsClassifier,
              "LogisticRegression": LogisticRegression}
    clf = models[select_model]()
    clf.fit(X_train, y_train.values.ravel())

    # roc_curve
    try:
        y_score = clf.predict_proba(X_test)[:, 1]
        fpr, tpr, thresholds = roc_curve(y_test, y_score)
        fig2 = px.area(
            x=fpr, y=tpr,
            title=f'ROC Curve (AUC={auc(fpr, tpr):.4f})',
            labels=dict(x='False Positive Rate', y='True Positive Rate'),
            width=700, height=500, template="plotly_white"
        )
        fig2.add_shape(
            type='line', line=dict(dash='dash'),
            x0=0, x1=1, y0=0, y1=1
        )

        fig2.update_yaxes(scaleanchor="x", scaleratio=1)
        fig2.update_xaxes(constrain='domain')

        # Precision-Recall Curve
        precision, recall, thresholds = precision_recall_curve(y_test, y_score)
        fig_pr = px.area(
            x=recall, y=precision,
            title=f'Precision-Recall Curve (AUC={auc(fpr, tpr):.4f})',
            labels=dict(x='Recall', y='Precision'),
            width=700, height=500,template="plotly_white"
        )
        fig_pr.add_shape(
            type='line', line=dict(dash='dash'),
            x0=0, x1=1, y0=1, y1=0
        )
        fig_pr.update_yaxes(scaleanchor="x", scaleratio=1)
        fig_pr.update_xaxes(constrain='domain')
    except:
        pass

    # confusion matrix
    cm = confusion_matrix(y_test, clf.predict(X_test))
    cm = cm.astype(int)
    fig_ = px.imshow(cm, title=f'Confusion Matrix',
                     labels=dict(x="Pred", y="True", color=""),
                     x=['Not active','Active'], y=['Not active','Active'], width=700, height=500,template="plotly_white")

    with st.beta_container():
        st.subheader("Model Plots: ")
        p1, p2, p3 = st.beta_columns((1, 1, 1))

        try:
            p1.plotly_chart(fig2, use_container_width=True)
        except:
            p1.write("Not applicable for this classifier")

        try:
            p2.plotly_chart(fig_pr, use_container_width=True)
        except:
            p2.write("Not applicable for this classifier")

        p3.plotly_chart(fig_, use_container_width=True)







