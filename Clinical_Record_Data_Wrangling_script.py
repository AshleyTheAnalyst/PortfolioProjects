import os
import re
import pandas as pd
import glob
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import statsmodels.api as sm
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency

# Read clinical information
clinical = pd.read_csv("/Users/ashleyli/Downloads/DataWranglingExercise_2023/DataWranglingExercise/ACME_clinical_listing_2023.tsv", sep="\t")
clinical['PID'] = clinical['ID'].str.extract('GNE\d{4}-\d{5}-(\d{5})')
# print(clinical)

# Read assay_1
assay_1_1 = pd.read_excel("/Users/ashleyli/Downloads/DataWranglingExercise_2023/DataWranglingExercise/assay_1/ACME0762_Assay1.xlsx", sheet_name = 'Assay_1_1')
assay_1_2 = pd.read_excel("/Users/ashleyli/Downloads/DataWranglingExercise_2023/DataWranglingExercise/assay_1/ACME0762_Assay1.xlsx", sheet_name = 'Assay_1_2')

# concatenate the two data frames
assay_1 = pd.merge(assay_1_1, assay_1_2, on='SAMID', how='outer')
assay_1.rename(columns={'INTERNAL_ID_x': 'INTERNAL_ID'}, inplace=True)
assay_1.drop(['INTERNAL_ID_y'], axis=1, inplace=True)
# print(assay_1)

assay_1['PID'] = assay_1['SAMID'].astype(str)
assay_1['PID'] = assay_1['PID'].str[-5:]
# print(assay_1['PID'])

assay_1 = assay_1.sort_values(by= 'PID')
# print(assay_1)

# Read assay_2
assay_2_files = glob.glob("/Users/ashleyli/Downloads/DataWranglingExercise_2023/DataWranglingExercise/assay_2/*/*", recursive=True)

assay2_data = []
for file in assay_2_files:
    temp_df = pd.read_csv(file)
    real_primary_id = re.search(r'PID-(\d+)', file).group(1).zfill(5)
    temp_df['PID'] = real_primary_id
    assay2_data.append(temp_df)

assay2_df = pd.concat(assay2_data)
assay2_pivot = assay2_df.pivot_table(values='measurement', index='PID', columns='analyte').reset_index()

# reorder the columns in assay2_pivot
def reorder_columns(df, column_order):
    original_columns = df.columns.tolist()
    for col in original_columns:
        if col not in column_order:
            column_order.append(col)
    df = df[column_order]
    
    return df

new_column_order = ['PID'] + [f'chemo_{i}' for i in range(1, 38)]

assay2_pivot = reorder_columns(assay2_pivot, new_column_order)

# Merge the datasets
assay2_pivot = assay2_pivot.sort_values(by= 'PID')
merged_df = clinical.merge(assay_1, on='PID').merge(assay2_pivot, on='PID')
# print(merged_df)

# use isna() to check for NA values in the dataframe
na_rows = merged_df[merged_df.isna().any(axis=1)]

# print out the rows with NA values
# print(na_rows)

# Check for missing values in column Var_1
missing_var1 = merged_df['Var_1'].isna().sum()
print('Number of missing values:\n', missing_var1)

# Calculate the percentage of missing values in column Var_1/the number of rows
missing_var1_pct = missing_var1 / len(merged_df) * 100
print('Percentage of missing values:\n', missing_var1_pct, '%')

# Check for missing values in column Var_1
missing_chemo1 = merged_df['chemo_1'].isna().sum()
print('Number of missing values in Var_1:\n', missing_var1)

# Calculate the percentage of missing values in column chemo_1/the number of rows
missing_chemo1_pct = missing_chemo1 / len(merged_df) * 100
print('Percentage of missing values in chemo_1:\n', missing_chemo1_pct, '%')

# Remove NaN row
# Only small amount of missing data in column Var_1 (<5%), so it would not affect the downstream plotting and just remove them directly
complete_records = merged_df.dropna()
# print(complete_records)

# output the file
merged_df.to_csv("merged_info.csv", sep="\t", header=True, index=True)

# output the file without any NA values
complete_records.to_csv("completed_info.csv", sep="\t", header=True, index=True)

# ============= alternative for Missing Data handling ==============

## Missing data evaluation to check if the data is random

# Perform the chi-square test for MCAR in columns Var_1 and chemo_1
observed = pd.crosstab(merged_df[['Var_1']].isnull().sum(axis=1), merged_df[['chemo_1']].isnull().sum(axis=1))
chi2, p, dof, expected = chi2_contingency(observed)
if p > 0.05:
    print('\nThe missing values are MCAR.\n')
else:
    print('\nThe missing values are not MCAR.\n')


## Missing data handling using mean imputation

# Mean imputation
mean_var = merged_df['Var_1'].mean()
# print(mean_var)
merged_df['Var_1'] = merged_df['Var_1'].fillna(mean_var)
# print(merged_df)

# output the file
merged_df.to_csv("merged_imputation_info.csv", sep="\t", header=True, index=True)

# ========================================

# Answer the questions

## Distinct variables
variables = complete_records.columns[7:].tolist()
print(f"Number of distinct variables (exclude ID, sex, DOB, active_smoker): {len(variables)}")
print(f"Variable name list: {variables}")

patient_count = len(complete_records)
patient_ids = list(complete_records['PID'])
print("Patients with complete records:", patient_count)
print("Patient ID list:", patient_ids)

# ==========================================

## Outlier Filtering

# calculate z-scores for each variable
z_scores = np.abs(stats.zscore(complete_records[['Var_1', 'chemo_1']]))

# filter data based on z-scores

threshold = 3.0
filtered_data = complete_records[(z_scores < threshold).all(axis=1)]
# print(filtered_data)

# ==========================================

## Plot the relationship between assay_1.Var_1 and assay_2.chemo_1 for each group

# Create a copy of the filtered_data DataFrame
filtered_data_copy = filtered_data.copy()

# Create binary variable for smoker (1) and non-smoker (0)
filtered_data_copy['smoker_binary'] = filtered_data_copy['active_smoker'].apply(lambda x: 1 if x else 0)

# Separate the data into treatment (smoke) and control group (non-smoker) based on sex
male_data = filtered_data_copy[filtered_data_copy['Sex'] == 'Male']
female_data = filtered_data_copy[filtered_data_copy['Sex'] == 'Female']

# Function to plot relationship and report Spearman correlation
def plot_relationship(data, title):
    sns.regplot(x='Var_1', y='chemo_1', data=data)
    plt.title(title)

    # Calculate and add the Spearman correlation to the plot
    spearman_corr, _ = spearmanr(data['Var_1'], data['chemo_1'])
    plt.text(0.1, 0.9, f'Spearman Correlation: {spearman_corr:.2f}', transform=plt.gca().transAxes)

# Plot for male smokers
plt.figure(figsize=(10, 5))
plt.subplot(121)
plot_relationship(male_data[male_data['smoker_binary'] == 1], 'Male Smokers')

# Plot for male non-smokers
plt.subplot(122)
plot_relationship(male_data[male_data['smoker_binary'] == 0], 'Male Non-Smokers')

# Plot for female smokers
plt.figure(figsize=(10, 5))
plt.subplot(121)
plot_relationship(female_data[female_data['smoker_binary'] == 1], 'Female Smokers')

# Plot for female non-smokers
plt.subplot(122)
plot_relationship(female_data[female_data['smoker_binary'] == 0], 'Female Non-Smokers')

plt.show()

# =============== alternative for Plotting ===================

## Plot the relationship between assay_1.Var_1 and assay_2.chemo_1 for each group

# Filter data for smokers and non-smokers
smokers = filtered_data_copy[filtered_data_copy['smoker_binary'] == 1]
non_smokers = filtered_data_copy[filtered_data_copy['smoker_binary'] == 0]

# Plot the relationship between Var_1 and chemo_1 variables for each sex and smoking status
def plot_relationship(data, title):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=data, x='Var_1', y='chemo_1', hue='Sex')
    
    # Calculate the Spearman correlation for each sex
    male_data = data[data['Sex'] == 'Male']
    female_data = data[data['Sex'] == 'Female']
    male_corr, _ = spearmanr(male_data['Var_1'], male_data['chemo_1'])
    female_corr, _ = spearmanr(female_data['Var_1'], female_data['chemo_1'])
    
    plt.title(f'{title} (Spearman correlation: Males = {male_corr:.2f}, Females = {female_corr:.2f})')
    plt.show()

plot_relationship(smokers, 'Smokers')
plot_relationship(non_smokers, 'Non-smokers')
