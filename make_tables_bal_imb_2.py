import os
import math
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import product
from settings.settings import (
    RESULTS_PATH,
    FROZEN,
    FINETUNED,
    REPRESENTATIONS,
    TASKS,
    TASKS_SHORT,
    PLM_PARAM_SIZE,
    LATEX_PATH,
    PLM_ORDER,
    PLM_ORDER_FINETUNED
)

DATASETS = ["balanced", "imbalanced"]

def show_values_on_bars(axs):
    def _show_on_single_plot(ax):
        for p in ax.patches:
            _x = p.get_x() + p.get_width() / 2
            _y = p.get_y() + p.get_height()
            value = f'{p.get_height():.2f}'
            ax.text(_x, _y - 0.1, value, ha="center")

    if isinstance(axs, np.ndarray):
        for idx, ax in np.ndenumerate(axs):
            _show_on_single_plot(ax)
    else:
        _show_on_single_plot(axs)

def show_delta_on_bars(axs, delta_values):
    def _show_on_single_plot(ax):
        half_bar_count = len(ax.patches) // 2
        for i in range(half_bar_count):
            p1 = ax.patches[i]
            p2 = ax.patches[i + half_bar_count]
            _x = (p1.get_x() + p1.get_width() / 2 + p2.get_x() + p2.get_width() / 2) / 2
            _y = max(p1.get_height(), p2.get_height()) + 0.02
            value = f'{delta_values[i]:.2f}'
            ax.text(_x, _y + 0.03, f'Δ = {value}', ha="center", fontsize=11, color='red')

    if isinstance(axs, np.ndarray):
        for idx, ax in np.ndenumerate(axs):
            _show_on_single_plot(ax)
    else:
        _show_on_single_plot(axs)

def extract_mean(value):
    return float(value.split("±")[0])

def extract_std(value):
    return float(value.split("±")[1])
    
representation_types = [FROZEN, FINETUNED]
precision_types = ["half", "full"]
representers = REPRESENTATIONS
tasks = TASKS
datasets = ["balanced", "imbalanced"]

# We read the csv file of the full results
df = pd.read_csv(os.path.join(RESULTS_PATH, "mean_balanced_imbalanced_results.csv"))
# Filter out the task "ionchannels_iontransporters"
df = df[df['Task'] != 'ionchannels_iontransporters']

balanced_df = df[df['Dataset'] == 'balanced']
imbalanced_df = df[df['Dataset'] == 'imbalanced']
df['MCC_mean'] = df['MCC'].apply(extract_mean)
df['MCC_std'] = df['MCC'].apply(extract_std)
df["plm_size"] = df["Representer"].apply(lambda x: PLM_PARAM_SIZE[x])
df['task_short'] = df['Task'].apply(lambda x: TASKS_SHORT[x])

# Group by Representer and Dataset, and calculate the mean MCC
mean_mcc = df.groupby(['task_short', 'Dataset'])['MCC_mean'].mean().reset_index()
std_mcc = df.groupby(['task_short', 'Dataset'])['MCC_std'].mean().reset_index()

delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'imbalanced']['MCC_mean'].values - mean_mcc[mean_mcc['Dataset'] == 'balanced']['MCC_mean'].values

# Create the bar plot
plt.figure(figsize=(10, 4))
barplot = sns.barplot(
    x='task_short',
    y='MCC_mean',
    hue='Dataset',
    data=mean_mcc,
    ci=None,
    palette="colorblind"
)

# X and Y axis labels
plt.xlabel("Task")
plt.ylabel("MCC")

# Add legend
plt.legend(title="Dataset")

# Add error bars
for i, p in enumerate(barplot.patches):
    x = p.get_x() + p.get_width() / 2
    y = p.get_height()
    err = std_mcc.loc[i, 'MCC_std']
    plt.errorbar(x, y, yerr=err, capsize=3, elinewidth=1.5, color='black', ls='none')

# Add MCC values on top of each bar
show_values_on_bars(barplot)

show_delta_on_bars(barplot, delta_mcc)
# Display the plot
# plt.show()
plt.savefig(os.path.join(LATEX_PATH, "mean_balanced_imbalanced_results_task.png"), bbox_inches='tight', dpi=300)
plt.close()



# Group by Representer and Dataset, and calculate the mean MCC
mean_mcc = df.groupby(['Classifier', 'Dataset'])['MCC_mean'].mean().reset_index()
std_mcc = df.groupby(['Classifier', 'Dataset'])['MCC_std'].mean().reset_index()

delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'imbalanced']['MCC_mean'].values - mean_mcc[mean_mcc['Dataset'] == 'balanced']['MCC_mean'].values


# Create the bar plot
plt.figure(figsize=(10, 4))
barplot = sns.barplot(
    x='Classifier',
    y='MCC_mean',
    hue='Dataset',
    data=mean_mcc,
    ci=None,
    palette="colorblind"
)

# X and Y axis labels
plt.xlabel("Classifier")
plt.ylabel("MCC")

# Add legend
plt.legend(title="Dataset")

# Add error bars
for i, p in enumerate(barplot.patches):
    x = p.get_x() + p.get_width() / 2
    y = p.get_height()
    err = std_mcc.loc[i, 'MCC_std']
    plt.errorbar(x, y, yerr=err, capsize=3, elinewidth=1.5, color='black', ls='none')

# Add Sensitivity values on top of each bar
show_values_on_bars(barplot)

show_delta_on_bars(barplot, delta_mcc)

# Display the plot
# plt.show()
plt.savefig(os.path.join(LATEX_PATH, "mean_balanced_imbalanced_results_classifier.png"), bbox_inches='tight', dpi=300)
plt.close()


# Group by Representer and Dataset, and calculate the mean MCC
mean_mcc = df.groupby(['plm_size', 'Dataset'])['MCC_mean'].mean().reset_index()
std_mcc = df.groupby(['plm_size', 'Dataset'])['MCC_std'].mean().reset_index()

# delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'imbalanced']['MCC_mean'] - mean_mcc[mean_mcc['Dataset'] == 'balanced']['MCC_mean']
delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'balanced'][['plm_size', 'MCC_mean']].reset_index(drop=True)
frozen_mcc_values = mean_mcc[mean_mcc['Dataset'] == 'imbalanced'][['plm_size', 'MCC_mean']].reset_index(drop=True)
delta_mcc['MCC_mean'] = [finetuned - frozen_mcc_values.loc[frozen_mcc_values['plm_size'] == plm_size, 'MCC_mean'].values[0] 
                         for plm_size, finetuned in zip(delta_mcc['plm_size'], delta_mcc['MCC_mean'])]

# We sort the values by plm_size the same as in PLM_ORDER_FINETUNED list
delta_mcc['plm_size'] = pd.Categorical(delta_mcc['plm_size'], categories=PLM_ORDER, ordered=True)
# Sort delta_mcc based on the plm_size column with the specified order
delta_mcc_sorted = delta_mcc.sort_values('plm_size')
# Reset the index of the sorted DataFrame
delta_mcc_sorted.reset_index(drop=True, inplace=True)

# Create the bar plot
plt.figure(figsize=(10, 4))
barplot = sns.barplot(
    x='plm_size',
    y='MCC_mean',
    hue='Dataset',
    data=mean_mcc,
    ci=None,
    palette="colorblind",
    order=PLM_ORDER
)

# X and Y axis labels
plt.xlabel("PLM (parameter size)")
plt.ylabel("MCC")

plt.xticks(fontsize=9)

# Add legend
plt.legend(title="Dataset", loc='lower left')

# Add error bars
for i, p in enumerate(barplot.patches):
    x = p.get_x() + p.get_width() / 2
    y = p.get_height()
    err = std_mcc.loc[i, 'MCC_std']
    plt.errorbar(x, y, yerr=err, capsize=3, elinewidth=1.5, color='black', ls='none')

# Add Sensitivity values on top of each bar
show_values_on_bars(barplot)

show_delta_on_bars(barplot, delta_mcc_sorted['MCC_mean'].values)

# Display the plot
# plt.show()
plt.savefig(os.path.join(LATEX_PATH, "mean_balanced_imbalanced_results_plm.png"), bbox_inches='tight', dpi=300)
plt.close()



# Filter DataFrame to only include frozen representation
finetuned_df = df[df['Representation'] == 'finetuned']

# Group by Representer and Dataset, and calculate the mean MCC
mean_mcc = finetuned_df.groupby(['plm_size', 'Dataset'])['MCC_mean'].mean().reset_index()
std_mcc = df.groupby(['plm_size', 'Dataset'])['MCC_std'].mean().reset_index()

df['plm_size'] = mean_mcc['plm_size'].astype('category')
df['Dataset'] = mean_mcc['Dataset'].astype('category')

diff_mcc = mean_mcc.pivot_table(values='MCC_mean', index='plm_size', columns='Dataset').reset_index()
diff_mcc['MCC_diff'] = diff_mcc['imbalanced'] - diff_mcc['balanced']

average_mcc_diff = diff_mcc['MCC_diff'].mean()

print(f"Average MCC difference: {average_mcc_diff}")

# delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'imbalanced']['MCC_mean'] - mean_mcc[mean_mcc['Dataset'] == 'balanced']['MCC_mean']
delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'imbalanced'][['plm_size', 'MCC_mean']].reset_index(drop=True)
frozen_mcc_values = mean_mcc[mean_mcc['Dataset'] == 'balanced'][['plm_size', 'MCC_mean']].reset_index(drop=True)
delta_mcc['MCC_mean'] = [finetuned - frozen_mcc_values.loc[frozen_mcc_values['plm_size'] == plm_size, 'MCC_mean'].values[0] 
                         for plm_size, finetuned in zip(delta_mcc['plm_size'], delta_mcc['MCC_mean'])]

# We sort the values by plm_size the same as in PLM_ORDER_FINETUNED list
delta_mcc['plm_size'] = pd.Categorical(delta_mcc['plm_size'], categories=PLM_ORDER_FINETUNED, ordered=True)
# Sort delta_mcc based on the plm_size column with the specified order
delta_mcc_sorted = delta_mcc.sort_values('plm_size')
# Reset the index of the sorted DataFrame
delta_mcc_sorted.reset_index(drop=True, inplace=True)

# Create the bar plot
plt.figure(figsize=(10, 4))
barplot = sns.barplot(
    x='plm_size',
    y='MCC_mean',
    hue='Dataset',
    data=mean_mcc,
    ci=None,
    palette="colorblind",
    order=PLM_ORDER_FINETUNED
)

# X and Y axis labels
plt.xlabel("PLM (parameter size)")
plt.ylabel("MCC")

plt.xticks(fontsize=9)

# Add legend
plt.legend(title="Dataset", loc='lower left')

# Add error bars
for i, p in enumerate(barplot.patches):
    x = p.get_x() + p.get_width() / 2
    y = p.get_height()
    err = std_mcc.loc[i, 'MCC_std']
    plt.errorbar(x, y, yerr=err, capsize=3, elinewidth=1.5, color='black', ls='none')

# Add MCC values on top of each bar
show_values_on_bars(barplot)

show_delta_on_bars(barplot, delta_mcc_sorted['MCC_mean'].values)

# Display the plot
# plt.show()
plt.savefig(os.path.join(LATEX_PATH, "mean_balanced_imbalanced_results_plm_finetuned.png"), bbox_inches='tight', dpi=300)
plt.close()

# Filter DataFrame to only include frozen representation
frozen_df = df[df['Representation'] == 'frozen']

# Group by Representer and Dataset, and calculate the mean MCC
mean_mcc = frozen_df.groupby(['plm_size', 'Dataset'])['MCC_mean'].mean().reset_index()
std_mcc = df.groupby(['plm_size', 'Dataset'])['MCC_std'].mean().reset_index()

df['plm_size'] = mean_mcc['plm_size'].astype('category')
df['Dataset'] = mean_mcc['Dataset'].astype('category')

diff_mcc = mean_mcc.pivot_table(values='MCC_mean', index='plm_size', columns='Dataset').reset_index()
diff_mcc['MCC_diff'] = diff_mcc['balanced'] - diff_mcc['imbalanced']

average_mcc_diff = diff_mcc['MCC_diff'].mean()

print(f"Average MCC difference: {average_mcc_diff}")



# delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'imbalanced']['MCC_mean'] - mean_mcc[mean_mcc['Dataset'] == 'balanced']['MCC_mean']
delta_mcc = mean_mcc[mean_mcc['Dataset'] == 'balanced'][['plm_size', 'MCC_mean']].reset_index(drop=True)
frozen_mcc_values = mean_mcc[mean_mcc['Dataset'] == 'imbalanced'][['plm_size', 'MCC_mean']].reset_index(drop=True)
delta_mcc['MCC_mean'] = [finetuned - frozen_mcc_values.loc[frozen_mcc_values['plm_size'] == plm_size, 'MCC_mean'].values[0] 
                         for plm_size, finetuned in zip(delta_mcc['plm_size'], delta_mcc['MCC_mean'])]

# We sort the values by plm_size the same as in PLM_ORDER_FINETUNED list
delta_mcc['plm_size'] = pd.Categorical(delta_mcc['plm_size'], categories=PLM_ORDER, ordered=True)
# Sort delta_mcc based on the plm_size column with the specified order
delta_mcc_sorted = delta_mcc.sort_values('plm_size')
# Reset the index of the sorted DataFrame
delta_mcc_sorted.reset_index(drop=True, inplace=True)

# Create the bar plot
plt.figure(figsize=(10, 4))
barplot = sns.barplot(
    x='plm_size',
    y='MCC_mean',
    hue='Dataset',
    data=mean_mcc,
    ci=None,
    palette="colorblind",
    order=PLM_ORDER
)

# X and Y axis labels
plt.xlabel("PLM (parameter size)")
plt.ylabel("MCC")

plt.xticks(fontsize=9)

# Add legend
plt.legend(title="Dataset", loc='lower left')

# Add error bars
for i, p in enumerate(barplot.patches):
    x = p.get_x() + p.get_width() / 2
    y = p.get_height()
    err = std_mcc.loc[i, 'MCC_std']
    plt.errorbar(x, y, yerr=err, capsize=3, elinewidth=1.5, color='black', ls='none')

# Add MCC values on top of each bar
show_values_on_bars(barplot)

show_delta_on_bars(barplot, delta_mcc_sorted['MCC_mean'].values)

# y limit to 1
plt.ylim(0, 1)

# Display the plot
# plt.show()
plt.savefig(os.path.join(LATEX_PATH, "mean_balanced_imbalanced_results_plm_frozen.png"), bbox_inches='tight', dpi=300)
plt.close()