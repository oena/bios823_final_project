0. Please install the following pkgs
```
! python3 -m pip install —-quiet xgboost
! python3 -m pip install --quiet lightgbm
! python3 -m pip install --quiet pandas_profiling
! python3 -m pip install --quiet yellowbrick
```

1. the first plot is comparing the results for different models. Because the virtual env we use is not compatible with the package `pycaret`, I can not call the API. So I run on my local machine and stored the result as a dataframe the made plot with it.

2. for the second part, I was meant to make a dropdown for the user to select which model she is going to use and then plot the `ROCAUC`, `PRCurve`, `LearningCurve`, `ConfusionMatrix`. But the yellowbrick package will mix all my outout jpgs together when I save them locally. I am still working on that to see if I can solve the ploblem. (TODO)

3. for the third part, there would be a data profiling report which is really cool and it runs well in jupyter notebook but I am not sure it can work in streamlit cause I never use it before. But I have make the profile report save to `.html` and `.json` file. Hope that can help the report to display in streamlit.