# -*- coding: utf-8 -*-
"""factor_premia_mp.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TVbVyogOqf20o1X_K9mpbO0FqzjqOTjY

# **The Bidirectional Relationship of Monetary Policy and Factor Premia**

## Dataset
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests
from sklearn.linear_model import LinearRegression
from mlxtend.feature_selection import SequentialFeatureSelector

pip install xlrd

pip install openpyxl

import xlrd
import openpyxl

from google.colab import drive
drive.mount('/content/drive')

"""# **Data Cleaning**

# I. Stance of Monetary Policy

When measuring the stance of monetary policy, Cooper (2020) use the following formula:
$$MP_t = FF_t - FF_t^* = FF_t - (RFF_t^* \ + 10Y IE)$$

where $MP_t$ is the stance of monetary policy, $FF_t$ is the federal funds rate, and $FF_t^*$ is the estimate of the (nominal) neutral rate ($FF^*$). Cooper (2020) set $FF^*$ as the sum of $RFF_t^*$ (the Laubach and Williams neutral real rate of interest) and $10Y IE$ (the Hoey-Philadelphia Fed Survey of Professional Forecasters (SPF) 10-year inflation expectations, as reported in the FRB/US data set).

Following that formula, we must merge those three components: $FF_t$, $RFF_t^*$, and $10Y IE$.

## A. Federal Funds Rate
"""

ffr = pd.read_excel('/content/drive/MyDrive/fedfunds.xls')
ffr.head()

"""What is the data type of the feature (1) "FEDFUNDS" and (2) observation_date? Question (1) is important because the federal funds raet is an element of the calculation of the stance of monetary policy. Question (2) is also vital becuase to merge this dataset with others, the dates have to be standardized."""

ffr.dtypes  #Check data type

"""(1) Currently, the dataframe has the federal funds rate as float type, which is the appropriate data type when computing the stance of monetary policy. So, we do not have to fchange the data type of this feature.

(2) We also don't have to change the "observation_date" since it is already in "datetime64." Meaning, if we had to change standardize the dates, that format meets the standard, and adapting that variable ("observation_date") when standardizing and merging will be easy.

### B. $RFF_t^*$
"""

#R star
rff = pd.read_excel('/content/drive/MyDrive/r_star.xlsx')

rff.rename(columns={'rstar': 'RSTAR'}, inplace=True)  #Match format and style of column title to other dataframes
rff.tail()

"""For similar reasons as for the federal funds rate, for the component $FF^*$, we must check the data type of "RSTAR" and "Date."
"""

rff.dtypes  #Check data type

"""The data types are the same as the federal funds rate in part A (Section I). So, no change is necessary.

## C. SPF 10-year Inflation Expectations
"""

#SPF 10 year inflation expectations
spf_10yr_inflation_exp = pd.read_excel('/content/drive/MyDrive/spf_10_yr_inflation_expectation.xlsx')
spf_10yr_inflation_exp.tail(10)

"""As for the other datasets, we must check the datatypes."""

spf_10yr_inflation_exp.dtypes

"""The datatype for the feature "INFCPI10YR" matches with the datatype of the federal funds rate and $FF^*$. However, the date for this dataset is set in two seperate columns: "YEAR" and "QUARTER." Also, they have an "integer" data type.

To perform operations, information must be the same type of data type as similar information in other dataframes. Specifically, the components of the stance of monetary policy must be float and the dates must be datetime format. In this case, value is a float. Also, the SPF 10-year inflation expectations have date in two seprate columns, making them integers.

## D. Standardize Dates

All datasets but "spf_10yr_inflation_exp" have monthly frequency. Monthly frequency can give more granular data. So, to delegate the different time frequencies, spf_10yr_inflation_exp must have monthly frequency instead of quarterly frequency when merging.

To achieve such a purpose, the "Date" column must be one and have a format similar to monthly frequency.
"""

months_dict = {1: '-01-01', 2: '-04-01', 3: '-07-01', 4: '-10-01'}  #Set dictionary that converts the quarters into month format

# Create "Date" column in monthly frequency
spf_10yr_inflation_exp['Date'] = spf_10yr_inflation_exp.apply(
    lambda row: pd.to_datetime(str(int(row['YEAR'])) + months_dict[int(row['QUARTER'])]), axis=1
)

spf_10yr_inflation_exp = spf_10yr_inflation_exp.drop(["YEAR", "QUARTER"], axis=1)     #Drop irrelevant columns

spf_10yr_inflation_exp.tail(10)

spf_10yr_inflation_exp.dtypes

"""As seen, now, the dates in quarterly frequency in the dataset are in one column and have been converted into monthly frequency. Also, the "Date" variable is in "datetime" format, as in other datasets.

## E. Merging & Calculating Stance of Monetary Policy

With the dates standardized across all datasets, they can be merged. Since rff and spf_10yr_inflation_exp as datasets have quarterly frequency, the values will be repeated across each quarter with forward fill starting from the first date r-star is available when merged with the federal funds rate (which is at a monthly frequency). This decision is made because monthly frequency will yield a more granular perspective.
"""

#Find the first date at which rr* is available
first_non_nan_row = spf_10yr_inflation_exp.loc[spf_10yr_inflation_exp['INFCPI10YR'].notna()].iloc[0]
print(first_non_nan_row)

#Drop all rows before 1991-10-01 in ffr dataset
ffr_filtered = ffr.loc[ffr["observation_date"] >= pd.to_datetime("1991-10-01")]

mp_stance = pd.merge(ffr_filtered, rff, left_on="observation_date", right_on="Date", how="left")
mp_stance["observation_date"] = pd.to_datetime(mp_stance["observation_date"] )
mp_stance['RSTAR'].fillna(method='ffill', inplace=True)   #Replace NaN values with forward fill
mp_stance = mp_stance.drop("Date", axis=1)

mp_stance.head(10)

mp_stance = pd.merge(mp_stance, spf_10yr_inflation_exp, left_on="observation_date", right_on="Date", how="left")
mp_stance['INFCPI10YR'].fillna(method='ffill', inplace=True)   #Replace NaN values with forward fill
mp_stance = mp_stance.drop("Date", axis=1)

mp_stance.tail(10)

"""Now, the dataset has all of the necessary components to calculate the monetary policy stance at a monthly frequency.

### F. Compute Monetary Policy Stance

Currenlty, the merged datast has all of the necessary components to calculate the monetary policy stance without the variable itself.
"""

mp_stance["MPSTANCE"] = mp_stance["FEDFUNDS"] - (mp_stance["RSTAR"] + mp_stance["INFCPI10YR"])    #Use formula

mp_stance = mp_stance.drop(["FEDFUNDS", "RSTAR", "INFCPI10YR"], axis=1)   #Drop irrelevant columns
mp_stance["observation_date"] = mp_stance["observation_date"].dt.strftime("%b-%Y") #Set month-year format to prepare for the merging with the x-variables

mp_stance.head(10)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

sns.set(style='ticks')

mp_stance_graph = mp_stance.copy()

if not pd.api.types.is_datetime64_dtype(mp_stance_graph['observation_date']):
    mp_stance_graph['observation_date'] = pd.to_datetime(mp_stance_graph['observation_date'])

fig, ax = plt.subplots(figsize=(10, 6))

sns.lineplot(data=mp_stance_graph, x='observation_date', y='MPSTANCE', ax=ax, linewidth=2)

ax.axhline(0, color='black', linewidth=1.5, linestyle='--')
ax.yaxis.set_tick_params(width=1.5, color='black')

# Set x-axis limits to 1991 and 2023:
ax.set_xlim([pd.to_datetime('1991-01-01'), pd.to_datetime('2023-12-31')])

# Adjust for yearly display with 5-year intervals:
ax.xaxis.set_major_locator(mdates.YearLocator(base=5))
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter("%Y %% 5"))
plt.xticks(rotation=45, ha='right')  # Rotate for readability
ax.set_xlabel('Year')

ax.set_title("A Measure of Stance of Monetary Policy")
ax.set_ylabel('Percentage (%)')
fig.tight_layout()
plt.show()

"""As seeen from the graph above, the measure of the stance of monetary policy matches with the original source, confirming the accuracy of the MPSTANCE as a variable.

## II. Factor Premia Across Asset Classes

### A. Change: Shape of Dataset

Ilmanen (2019) publish and update a dataset of factor premia across different asset classes. The first 30 rows of the uploaded dataset show empty values and unnamed column names.
"""

factor_premia = pd.read_excel('/Century of Factor Premia Monthly.xlsx')
factor_premia.head(30)

#Fix the shape of the dataframe

#Set columns
factor_premia.columns = factor_premia.iloc[17]  #Column headers
clean_factor_premia = factor_premia[18:]

clean_factor_premia.tail(10)

"""After setting the right column names and deleting the irrelevant first 16 rows, the factor premia dataset now has relevant column names and values fitting for factor premia.

### B. Change: Change Data Type

To conduct regressions, factor premia have to be float. Currently, their data type is "object."
"""

clean_factor_premia.dtypes

for column in clean_factor_premia.columns[1:]:
    clean_factor_premia[column] = clean_factor_premia[column].astype(float)

clean_factor_premia.dtypes

"""Now, X-variables have float type. So, regression analysis can be conducted.

After making the factor premia dataset legible and preparing it for regression analysis, can it be merged with the monetary policy stance as a y-variable?
"""

clean_factor_premia.rename(columns={clean_factor_premia.columns[0]: "Date"}, inplace=True)    #Set clear title for column of dates
clean_factor_premia["Date"] = pd.to_datetime(clean_factor_premia["Date"])   #Set in standardized format (datetime)
# clean_factor_premia = clean_factor_premia.drop('Date_month_year', axis=1)

clean_factor_premia.dtypes

"""Without a clear name and standardized format for the dates, merging and understanding the datasest will be hard.

## III. Merging Factor Premia and Stance of MP

The two datasets - mp_stance and clean_factor_premia - will be merged at their respectve columns for dates. How compatible are the dates?
"""

#Ensure they have the same data type
mp_stance["observation_date"] = pd.to_datetime(mp_stance["observation_date"])
clean_factor_premia["Date"] = pd.to_datetime(clean_factor_premia["Date"])

#Set them as month-year only (days can differ)
mp_stance["observation_month_year"] = mp_stance["observation_date"].dt.strftime("%b-%Y")
clean_factor_premia["Date_month_year"] = clean_factor_premia["Date"].dt.strftime("%b-%Y")

"""Now, both datasets can be merged."""

monthly_full_df = pd.merge(mp_stance, clean_factor_premia, left_on="observation_month_year", right_on="Date_month_year", how='inner')

monthly_full_df.set_index(monthly_full_df["Date"], inplace=True)  #Set the dates as index for regression analysis
monthly_full_df = monthly_full_df.drop(['observation_date', 'observation_month_year', 'Date', 'Date_month_year'], axis=1)

monthly_full_df.head(10)

"""### Check for Empty Values

Looking at the merged dataset, some variables have empty values, which will interrupt regression analysis.
"""

# Find when "Date" is NaN
nan_date_rows = monthly_full_df[monthly_full_df.index.isna()]
print(nan_date_rows)

"""Merged dataset has no empty values. So, it seems ready for regression

## Check Data Type

Regression analysis requires quantitative variables. So, does the dataset has the right type of data type?
"""

monthly_full_df.dtypes

"""The dataset has all variables as "float," an appropriate data type for regression analysis.

## Descriptive Statistics

How ready is the dataset for regression analysis?
"""

descriptive_stats = monthly_full_df.describe(include='all')
transposed_stats = descriptive_stats.transpose()
transposed_stats

"""The provided summary statistics are consistent and show values for each variable, proving that the merging was logical, data cleaning was correct, and the data is in a suitable state for regression analysis."""



"""## IV. Regression Analysis: Factor Premia Accross Asset Class and Monetary Policy Stance

Which x-variables from the merged dataset should we consider? The x-variables in the merged dataset give an opportunity for multicollinearity since "Fixed Income" as an asset class has its returns disaggregated based on factors. At the same time, the merged dataset has the returns of "Fixed Income" as an asset class and the returns of each of the factors with all of the asset classes aggregated.

The dataset can be used in many ways. To utilize the full potential of assset class and factor premia units, I will investigate the possible relationship between factor premia across asset class as the drivers of the monetary policy stance. With this goal, what should be the x-variables?
"""

monthly_factor_asset_y = monthly_full_df["MPSTANCE"]

# Get all columns above "All Stock Selection Value"
monthly_factor_asset_X = monthly_full_df.iloc[:, 1:monthly_full_df.columns.get_loc("All Stock Selection Value")]

"""###**A. OLS Regression**

How can we assess the usefuleness of the dataset? The dataset must be able to provide useful statistical insight.
"""

X = monthly_factor_asset_X
y = monthly_factor_asset_y

X = sm.add_constant(X)

#Fit OLS regrssion
ols_model = sm.OLS(y, X).fit()

print(ols_model.summary())

"""For this reason, we implement OLS regression. To assess the appropriatedness of OLS regression, we examine r-squared. It is at 7.8%, hinting that, perhaps, OLS regression may be inappropriate.

### **B. Stepwise Regression**

Perhaps, OLS regression did not seem to be the best statistical method because it had a large number of x-variables, including features that do not contribute to the statistical signficance of OLS regression.
"""

X = sm.add_constant(X)

estimator = LinearRegression()

# Run stepwise regression
stepwise_selector = SequentialFeatureSelector(estimator=estimator,
                                              k_features='best',
                                              forward=True,
                                              scoring='r2',
                                              cv=0)   #Number of folds
stepwise_selector.fit(X, y)
selected_features = list(stepwise_selector.k_feature_names_)
dropped_features = list(set(X.columns) - set(selected_features))

# Fit model with selected features
final_model = sm.OLS(y, X[selected_features]).fit()

stepwise_model_summary = final_model.summary()
print(stepwise_model_summary)

#Give any dropped features
if dropped_features:
    print(f"Dropped features: {dropped_features}.")
else:
    print(f"No features were dropped during stepwise regression.")

"""R-squared decreased as features were dropped during stepwise regression, as seen above. Perhaps, stepwise regression and OLS regression are not appropriate models.

### **C. Lagged Variables**

An alternative explanation can be lagged effects. To test this theory, we try to find the most optimal number of lags for each explanatory variable.
"""

def find_best_lags(x_columns, y_variable, data_frame):
    results = []

    for column in x_columns:
        best_lag = None
        best_p_value = float('inf')
        x_values = data_frame[column].values
        y_values = data_frame[y_variable].values

        for lag in range(1, 13):
            test_data = pd.DataFrame({'x': x_values, 'y': y_values})

            # Perform Granger causality test
            results_dict = grangercausalitytests(test_data, maxlag=lag, verbose=False)
            p_value = results_dict[lag][0]['params_ftest'][1]

            if p_value < best_p_value:
                best_lag = lag
                best_p_value = p_value

        results.append({'Column': column, 'Best Lag': best_lag})

    results_df = pd.DataFrame(results)
    return results_df

lagged_X = [col for col in monthly_factor_asset_X.columns if col != "MPSTANCE"]
lagged_y = "MPSTANCE"

lag_results = find_best_lags(lagged_X, lagged_y, monthly_full_df)
print(lag_results)

"""These lag values can help create a new dataframe that can potentially better understand monetary policy stance. How can we create such a dataset?"""

def create_lagged_dataframe(x_columns, y_variable, data_frame):
    results = []

    for column in x_columns:
        best_lag = None
        best_p_value = float('inf')
        x_values = data_frame[column].values
        y_values = data_frame[y_variable].values

        test_data = pd.DataFrame({'x': x_values, 'y': y_values})

        # Run Granger causality test with the maximum lag value as 12
        results_dict = grangercausalitytests(test_data, maxlag=12, verbose=False)

        for lag, result in results_dict.items():
            p_value = result[0]['params_ftest'][1]
            if p_value < best_p_value:
                best_lag = lag
                best_p_value = p_value

        results.append({'Column': column, 'Best_Lag': best_lag})

    results_df = pd.DataFrame(results)

    # Create lagged DataFrame
    lagged_df = pd.DataFrame()
    for row in results_df.itertuples():
        column_name = row.Column
        lag = row.Best_Lag
        lagged_df[f'{column_name}_lag{lag}'] = data_frame[column_name].shift(lag)

    return lagged_df

lagged_monthly_factor_asset = create_lagged_dataframe(lagged_X, lagged_y, monthly_full_df)

lagged_monthly_factor_asset

"""Dataset has missing values when incorporating lagged values. So, we drop the first few rows with the amount being the largest lag value, explaining the importance of "lag_results" table.  """

# Find the largest lag value
largest_lag = lag_results['Best Lag'].max()

# Drop rows given largest lag for lagged_monthly_factor_asset to not have missing values
lagged_monthly_factor_asset = lagged_monthly_factor_asset.iloc[largest_lag:]

lagged_monthly_factor_asset

"""Now, it has no empty values, which helps conduct regression analysis."""

no_na_in_first_row = lagged_monthly_factor_asset.iloc[0, :].isnull().sum() == 0

# Print the result
if no_na_in_first_row:
    print("No NaN values in the first row after dropping the largest lag value.")
else:
    print("NaN values present in the first row after dropping the largest lag value.")

lag_df = pd.merge(monthly_full_df["MPSTANCE"], lagged_monthly_factor_asset, left_on=monthly_full_df.index, right_on = lagged_monthly_factor_asset.index, how="inner")
lag_df = lag_df.drop(['key_0'], axis=1)
lag_df

"""###**A. OLS Regression**

R-square of OLS regression increased from 7.8% to 10.8% by including the most optimal lags for each explanatory variables. At the same time, adjusted r-squared increased from 1.1% to 3.6%.
"""

#Set variables
lagged_y = lag_df["MPSTANCE"]
lagged_X = lag_df.iloc[:, 1:]

# Add a constant column to X
lagged_X = sm.add_constant(lagged_X)

# Fit the OLS model
lag_ols = sm.OLS(lagged_y, lagged_X).fit()

# Print the summary statistics
print(lag_ols.summary())

"""### **B. Stepwise Regression**

When considering lagged effects in stepwise regression, the model does not drop any features, yet the r-squared largely increased from 7.8% to 26.3% and adjusted r-squared increased from 1.1% to 20.3% without any number of folds.
"""

import pandas as pd
import statsmodels.api as sm
from mlxtend.feature_selection import SequentialFeatureSelector

estimator = LinearRegression()

stepwise_selector = SequentialFeatureSelector(
    estimator=estimator,
    k_features='best',
    forward=True,
    scoring='r2',
    cv=0  #Number of folds
)

stepwise_selector.fit(lagged_X, lagged_y)

selected_features = list(stepwise_selector.k_feature_names_)
dropped_features = list(set(lagged_X.columns) - set(selected_features))

# Fit model using selected features
final_model = sm.OLS(lagged_y, lagged_X[selected_features]).fit()

lag_stepwise_summary = final_model.summary()
print(lag_stepwise_summary)

# Print the dropped features, if any
if dropped_features:
    print(f"Dropped features: {dropped_features}.")
else:
    print(f"No features were dropped during stepwise regression.")

"""### **A. Collinearity**

Why did r-squared improve significantly when stepwise regression did not drop any features? Perhaps, r-squared improved due to collinearity.
"""

lagged_X = lag_df.iloc[:, 1:]

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

vif_scores = pd.DataFrame()
vif_scores["VIF Factor"] = [variance_inflation_factor(lagged_X.values, i) for i in range(lagged_X.shape[1])]
vif_scores["Feature"] = lagged_X.columns

vif_scores.set_index('Feature', inplace=True)

vif_scores

"""The above results show that collinearity is a concern for some features - "US Stock Selection Momentum_lag6" and "Intl Stock Selection Momentum_lag6" - but for most features, collinearity is not an issue since their VIF is less than 5.

### **B. Overfitting**

An alternative explanation for such a sharp improvement in r-squared is overfitting. To what extent can that be an explanation?
"""

estimator = LinearRegression()

stepwise_selector = SequentialFeatureSelector(
    estimator=estimator,
    k_features='best',
    forward=True,
    scoring='r2',
    cv=5  # Change number of folds
)

stepwise_selector.fit(lagged_X, lagged_y)

selected_features = list(stepwise_selector.k_feature_names_)
dropped_features = list(set(lagged_X.columns) - set(selected_features))

final_model = sm.OLS(lagged_y, lagged_X[selected_features]).fit()

lag_overfitting_stepwise_summary = final_model.summary()
print(lag_overfitting_stepwise_summary)

"""When increasing the number of folds to 5, r-squared increased from 7.8% to 18.4% instead of 26.3%. This marginal decrease shows that overfitting may explain some of the inflated r-squared; however, perhaps, factor premia as lagged features may help explain the stance of monetary policy."""

# Print the dropped features, if any
if dropped_features:
    print(f"Dropped features: {dropped_features}.")
else:
    print(f"No features were dropped during stepwise regression.")

"""When increasing folds, stepwise regression dropped features stressing that overfitting occured in the model with no fold. Factor premia as lagged variables have promise, but further investigation is required."""





