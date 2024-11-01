import pandas as pd
import os
from settings import settings
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# We read the csv file of the full results
df = pd.read_csv(os.path.join(settings.RESULTS_PATH,
                 "mean_balanced_imbalanced_results.csv"))

# The dataframe has the following columns: "Task", "Dataset", "Representation", "Representer", "Precision", "Classifier", "MCC"


# We make a new dataframe out of the df dataframe, focusing on the Dataset column.
# The new dataframe has the following columns: "Task", "Dataset", where we group by the representer under each category of "Task", "Dataset".
# Then we take the best MCC value for each category of "Task", "Dataset".

representation_types = [settings.FROZEN, settings.FINETUNED]
precision_types = ["half", "full"]
representers = settings.REPRESENTATIONS
# We use TASKS_SHORT dictionary to shorten the names of the tasks with the keys the long names and the values the short names
tasks = settings.TASKS
datasets = ["balanced", "imbalanced"]

ds_best_mcc = []
for task in tasks:
    for dataset in datasets:
        df_temp = df[(df["Task"] == task) & (df["Dataset"] == dataset)]
        if not df_temp.empty:
            for representer in representers:
                df_temp2 = df_temp[df_temp["Representer"]
                                   == representer["name"]]
                if not df_temp2.empty:
                    # We take the first three rows of the df_temp2 sorted by MCC value split by "±" and take the first element
                    three_best_mcc = df_temp2["MCC"].str.split(
                        "±").str[0].astype(float).nlargest(3).index.tolist()
                    df_three_best_mcc = df_temp2.loc[three_best_mcc]

                    # We take the best MCC value for each category of "Task", "Dataset" and "Representer"
                    best_mcc_id = df_temp2["MCC"].str.split(
                        "±").str[0].astype(float).idxmax()

                    best_mcc = df_temp2.loc[best_mcc_id, "MCC"]
                    ds_best_mcc.append(
                        [representer["name"], settings.TASKS_SHORT[task], dataset, best_mcc])

# We create the dataframe with columns "PLM", "IC-MP Balanced", "IC-MP Imbalanced", "IT-MP Balanced, "IT-MP Imbalanced"
df_table = pd.DataFrame(ds_best_mcc, columns=["PLM", "Task", "Dataset", "MCC"])
# Create a new column 'Task-Dataset' by combining 'Task' and 'Dataset' columns
df_table['Task-Dataset'] = df_table['Task'] + ' ' + df_table['Dataset']

# Pivot the DataFrame to the desired structure
df_table = df_table.pivot(index='PLM', columns='Task-Dataset', values='MCC')

# Reset the index
df_table.reset_index(inplace=True)

# Rename the index
df_table.index.name = None

# Convert the 'PLM' column to a categorical data type with the specified custom order
df_table['PLM'] = pd.Categorical(df_table['PLM'], categories=[
                                 representer["name"] for representer in representers], ordered=True)

# Sort the DataFrame based on the custom order of the 'PLM' column
df_table.sort_values(by='PLM', inplace=True)

# Reset the index
df_table.reset_index(drop=True, inplace=True)

# We create a latex table from the dataframe with the header boldface
latex_table = df_table.to_latex(
    index=False, escape=True, column_format='l' + 'c' * (len(df_table.columns) - 1))

# Replace the column names with their boldface versions
for col in df_table.columns:
    latex_table = latex_table.replace(col, '\\textbf{' + col + '}')

# Save the modified LaTeX table to a file
with open(os.path.join(settings.LATEX_PATH, "mean_balanced_imbalanced_results.tex"), 'w') as f:
    f.write(latex_table)

# Melt the DataFrame to 'long' format for easier plotting with Seaborn
df_table_melted = df_table.melt(
    id_vars='PLM', var_name='Task-Dataset', value_name='MCC')

# # Split the MCC column into two separate columns for mean and std deviation
# df_table_melted[['Mean', 'Error']] = df_table_melted['MCC'].str.split('±', expand=True).astype(float)

# # Create a new column to represent dataset balance status
# df_table_melted['Balance'] = df_table_melted['Task-Dataset'].apply(lambda x: 'Imbalanced' if 'imbalanced' in x else 'Balanced')

# # Create the scatter plot with unique symbols/colors per PLM and error bars
# plt.figure(figsize=(12, 6))
# sns.scatterplot(data=df_table_melted, x='Balance', y='Mean', hue='PLM', style='PLM', s=100)

# # Add error bars to the scatter plot
# for index, row in df_table_melted.iterrows():
#     plt.errorbar(x=row['Balance'], y=row['Mean'], yerr=row['Error'], fmt='none', capsize=5, color='black', alpha=0.6)

# # plt.title('Scatter Plot with Error Bars for PLMs and Dataset Balance')
# plt.ylabel('MCC')
# plt.savefig(os.path.join(settings.LATEX_PATH,
#             "mean_balanced_imbalanced_results_line_scatter.png"), dpi=300, bbox_inches='tight')

# plt.close()


# Split the MCC column into two separate columns for mean and std deviation
df_table_melted[['Mean', 'Error']] = df_table_melted['MCC'].str.split('±', expand=True).astype(float)

sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.5)
sns.set_palette("colorblind")

# Group the data by PLM and Task-Dataset, calculate the mean and standard deviation of MCC
grouped_data = df_table_melted.groupby(['PLM', 'Task-Dataset']).agg({'Mean': 'mean', 'Error': 'mean'}).reset_index()

# Further aggregate the data by PLM and balance status (balanced or imbalanced)
grouped_data['Balance'] = grouped_data['Task-Dataset'].apply(lambda x: 'Imbalanced' if 'imbalanced' in x else 'Balanced')
final_data = grouped_data.groupby(['PLM', 'Balance']).agg({'Mean': 'mean', 'Error': 'mean'}).reset_index()

# Create the bar plot
plt.figure(figsize=(15, 6))
barplot = sns.barplot(data=final_data, x='PLM', y='Mean', hue='Balance', capsize=0.1, ci=None)

# Add error bars
for i, p in enumerate(barplot.patches):
    x = p.get_x() + p.get_width() / 2
    y = p.get_height()
    err = final_data.loc[i, 'Error']
    plt.errorbar(x, y, yerr=err, capsize=3, elinewidth=1.5, color='black', ls='none')

# The legend with title "Dataset"
plt.legend(title='Dataset', loc='lower right')

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

# Add MCC values on top of each bar
show_values_on_bars(barplot)

# Calculate delta and display between the bars
delta = final_data.pivot_table(index='PLM', columns='Balance', values='Mean').reset_index()
delta['Delta'] = delta['Imbalanced'] - delta['Balanced']

for index, row in delta.iterrows():
    x = row.name + 0.25
    y = max(row['Balanced'], row['Imbalanced'])
    delta_value = row['Delta']
    plt.text(x - 0.25, y + 0.02, f'Δ={delta_value:.2f}', ha="center", fontsize=12, color='red', fontweight='bold')

plt.ylabel('Mean MCC')
# Save the plot to a file
plt.savefig(os.path.join(settings.LATEX_PATH,
            "mean_balanced_imbalanced_results_bar_plot_delta.png"), dpi=300, bbox_inches='tight')

plt.close()

df_table_melted['MCC'] = df_table_melted['MCC'].apply(
    lambda x: float(x.split('±')[0]))

sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.5)
sns.set_palette("colorblind")

# Create the bar plot using Seaborn
plt.figure(figsize=(10, 4))
ax = sns.barplot(x='PLM', y='MCC', hue='Task-Dataset', data=df_table_melted)

# Customize the plot
# plt.title('Impact of Balanced and Imbalanced Datasets on PLMs')
plt.xlabel('Protein Language Models')
plt.ylabel('MCC')
plt.legend(loc='lower right', fontsize=8)

# Set the y-axis limits
plt.ylim(0.4)

# Loop through each bar in the plot
for p in ax.patches:
    # Get the bar's x and y coordinates and its height
    x = p.get_x() + p.get_width() / 2
    y = p.get_height()
    height = p.get_height()
    # Write the value of the bar on top of it
    ax.text(x, y, f'{height:.2f}', ha='center', va='bottom', fontsize=8)

# plt.show()
# Save the plot
plt.savefig(os.path.join(settings.LATEX_PATH,
            "mean_balanced_imbalanced_results.png"), dpi=300, bbox_inches='tight')

plt.close()

# Pivot the dataframe to create a matrix of MCC values
df_pivot = df_table_melted.pivot('PLM', 'Task-Dataset', 'MCC')

# Create the heatmap using Seaborn
plt.figure(figsize=(10, 4))
ax1 = sns.heatmap(df_pivot, annot=True, cmap="coolwarm", xticklabels=True, cbar=True)

ax1.set_xlabel('')
ax1.set_ylabel('')

# plt.tight_layout()
# plt.show()

plt.savefig(os.path.join(settings.LATEX_PATH,
            "mean_balanced_imbalanced_results_heatmap.png"), dpi=300, bbox_inches='tight')
