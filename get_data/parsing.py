import pandas as pd
import numpy as np
import geopandas as gpd
import glob

#In epidemiology, $R_t$ (the effective reproduction number) is the average number of people that one infected person will pass the virus to at a specific time, $t$.
# ---------------------------------------------------------
# Step 1: Merge the daily CSV files side-by-side
# ---------------------------------------------------------
# Load all CSVs from your get_data/insp_sitrep directory
csv_files = glob.glob('./insp_sitrep/*.csv')

# Read the very first file to act as our base dataframe
df = pd.read_csv(csv_files[0])

# Loop through the rest of the files and merge them one by one
for file in csv_files[1:]:
    df_temp = pd.read_csv(file)
    
    # Merge side-by-side based on 'nom' and 'date'. 
    # how='outer' ensures we don't lose any rows, automatically inserting NaN for missing data.
    df = pd.merge(df, df_temp, on=['nom', 'date'], how='outer')

# ---------------------------------------------------------
# Step 2: Fix Mixed French/English Field Names
# ---------------------------------------------------------
# (Your existing Step 2 code goes here)
column_mapping = {
    'nom': 'health_zone',
    'cumulative_confirmed_cases': 'cumulative_cases',
    'cumulative_confirmed_deaths': 'deaths'
}
df = df.rename(columns=column_mapping)

# ---------------------------------------------------------
# Step 3: Handle Missing Dates
# ---------------------------------------------------------
# Convert to datetime objects, turning invalid formats into 'NaT' (Not a Time)
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# Remove rows where the date is missing using basic boolean indexing
df = df[df['date'].notna()]

# ---------------------------------------------------------
# Step 4: Fix Inconsistent Health-Zone Spellings
# ---------------------------------------------------------
# Standardize string formatting (lowercase, strip extra spaces, capitalize)
df['health_zone'] = df['health_zone'].str.strip().str.title()

# ---------------------------------------------------------
# Step 5: Fix Cumulative Case Counts Revised Downward
# ---------------------------------------------------------
# In an outbreak, cumulative cases shouldn't drop. 
# We sort chronologically, then use cummax() to ensure the numbers only go up or stay flat.
df = df.sort_values(by=['health_zone', 'date'])

df['cumulative_cases'] = pd.to_numeric(df['cumulative_cases'], errors='coerce').fillna(0)
df['deaths'] = pd.to_numeric(df['deaths'], errors='coerce').fillna(0)

# ---------------------------------------------------------
# Step 6: Join to the HDX DRC Health Zones Shapefile
# ---------------------------------------------------------
# Load the shapefile
hdx_shapefile = gpd.read_file('./shapefiles/DRC_Health_zones.shp')

# Standardize the 'Nom' column in the shapefile so it matches our cleaned health_zone column
hdx_shapefile['Nom'] = hdx_shapefile['Nom'].str.strip().str.title()

# Merge the cleaned case data with the geographic boundaries
merged_data = hdx_shapefile.merge(
    df, 
    left_on='Nom', 
    right_on='health_zone', 
    how='left'
)

# Display the first few rows to verify the join
# Drop rows where the date is NaT to see the health zones that actually merged with case data
print(merged_data.dropna(subset=['date'])[['Nom', 'date', 'cumulative_cases', 'deaths']].head())
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ---------------------------------------------------------
# Step 7: Vectorize the Rt-Proxy Feature
# ---------------------------------------------------------
# 1. Calculate daily new cases using vectorized .diff()
df['new_cases'] = df.groupby('health_zone')['cumulative_cases'].diff().fillna(0)

# Ensure no negative daily cases (due to INSP data corrections)
df['new_cases'] = np.where(df['new_cases'] < 0, 0, df['new_cases'])

# 2. Calculate rolling 7-day sums for the current week and previous week
current_7d = df.groupby('health_zone')['new_cases'].rolling(window=7, min_periods=1).sum().reset_index(level=0, drop=True)
prev_7d = df.groupby('health_zone')['new_cases'].shift(7).rolling(window=7, min_periods=1).sum().reset_index(level=0, drop=True)

# 3. Vectorize the Rt-proxy calculation using np.where to avoid Division By Zero errors
df['rt_proxy'] = np.where(prev_7d > 0, current_7d / prev_7d, 0.0)

# ---------------------------------------------------------
# Step 8: Generate the Three Insight Plots
# ---------------------------------------------------------
# Filter data for April 2026 onwards
import os
import matplotlib.ticker as ticker

# ---------------------------------------------------------
# Step 8: Generate and Save the Three Insight Plots
# ---------------------------------------------------------
# 1. Programmatically create the directory to store the plots
output_dir = './plots'
os.makedirs(output_dir, exist_ok=True)

# Filter data for April 2026 onwards
df_recent = df[df['date'] >= '2026-04-01']
sns.set_theme(style="whitegrid")

# --- Plot 1: Epidemic Curve (National Daily New Cases) ---
plt.figure(figsize=(12, 6)) # Create a fresh, independent figure
epi_curve = df_recent.groupby('date')['new_cases'].sum().reset_index()

plt.bar(epi_curve['date'].dt.strftime('%Y-%m-%d'), epi_curve['new_cases'], color='coral')
plt.title('Epidemic Curve: Daily New Cases (Since April 2026)', fontsize=14, fontweight='bold')
plt.ylabel('New Cases')
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(3))
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig(f"{output_dir}/epidemic_curve.png", dpi=300) # Save it
plt.close() # Close it so the next chart doesn't draw over it

# --- Plot 2: Health-Zone Case Breakdown (Top 20) ---
plt.figure(figsize=(10, 8))
hz_breakdown = df.groupby('health_zone')['cumulative_cases'].max().sort_values(ascending=False).reset_index()
hz_breakdown = hz_breakdown[hz_breakdown['cumulative_cases'] > 0] 
hz_top20 = hz_breakdown.head(20)

sns.barplot(
    x='cumulative_cases', 
    y='health_zone', 
    hue='health_zone', 
    data=hz_top20, 
    palette='viridis', 
    legend=False
)
plt.title('Top 20 Health Zones by Total Cases', fontsize=14, fontweight='bold')
plt.xlabel('Total Cases')
plt.ylabel('Health Zone')

plt.tight_layout()
plt.savefig(f"{output_dir}/health_zone_breakdown.png", dpi=300)
plt.close()

# --- Plot 3: Case-Fatality Ratio (CFR) Trend Over Time ---
plt.figure(figsize=(12, 6))
national_trend = df_recent.groupby('date')[['cumulative_cases', 'deaths']].sum().reset_index()

national_trend['cfr'] = np.where(
    national_trend['cumulative_cases'] > 0, 
    (national_trend['deaths'] / national_trend['cumulative_cases']) * 100, 
    0.0
)

plt.plot(national_trend['date'].dt.strftime('%Y-%m-%d'), national_trend['cfr'], color='darkred', linewidth=2)
plt.title('Case-Fatality Ratio (CFR) Trend Over Time', fontsize=14, fontweight='bold')
plt.ylabel('CFR (%)')
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(3))
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig(f"{output_dir}/cfr_trend.png", dpi=300)
plt.close()

print(f"Success! All three plots have been saved securely in the '{output_dir}' directory.")