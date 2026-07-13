import pandas as pd
import numpy as np
import glob
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

base_path = "data/external/BDBV2026-Data/data/"
sitrep_path = os.path.join(base_path, "insp_sitrep")

cases_path = glob.glob(os.path.join(sitrep_path, "**/*cumulative_confirmed_cases*.csv"), recursive=True)[0]
deaths_path = glob.glob(os.path.join(sitrep_path, "**/*cumulative_confirmed_deaths*.csv"), recursive=True)[0]

cases_df = pd.read_csv(cases_path)
cases_df.columns = cases_df.columns.str.lower().str.strip()
cases_df = cases_df.rename(columns={'nom': 'health_zone', 'cumulative_confirmed_cases': 'confirmed_cases'})

deaths_df = pd.read_csv(deaths_path)
deaths_df.columns = deaths_df.columns.str.lower().str.strip()
deaths_df = deaths_df.rename(columns={'nom': 'health_zone', 'cumulative_confirmed_deaths': 'deaths'})

raw_df = pd.merge(cases_df, deaths_df, on=['health_zone', 'date'], how='outer')
raw_df['deaths'] = raw_df['deaths'].fillna(0)

aliases_df = pd.read_csv(os.path.join(base_path, "aliases.csv"))
alias_dict = dict(zip(aliases_df.iloc[:, 0], aliases_df.iloc[:, 1]))

raw_df['health_zone'] = raw_df['health_zone'].replace(alias_dict)
raw_df['date'] = pd.to_datetime(raw_df['date'], errors='coerce')
df = raw_df.dropna(subset=['date', 'health_zone']).sort_values(['health_zone', 'date'])

df['confirmed_cases'] = pd.to_numeric(df['confirmed_cases'], errors='coerce').fillna(0)
df['deaths'] = pd.to_numeric(df['deaths'], errors='coerce').fillna(0)

df['confirmed_cases'] = df.groupby('health_zone')['confirmed_cases'].cummax()
df['deaths'] = df.groupby('health_zone')['deaths'].cummax()

df['new_cases'] = df.groupby('health_zone')['confirmed_cases'].diff().fillna(df['confirmed_cases'])
df['new_cases'] = df['new_cases'].clip(lower=0)

shapefile_path = glob.glob(os.path.join(base_path, "shapefiles", "**", "*.shp"), recursive=True)[0]
gdf = gpd.read_file(shapefile_path)

gdf['Nom'] = gdf['Nom'].replace(alias_dict) 
merged_map_df = gdf.merge(df, left_on='Nom', right_on='health_zone', how='left')

national_df = df.groupby('date')[['new_cases']].sum().reset_index()
national_df = national_df.sort_values('date')

cases_array = national_df['new_cases'].to_numpy()
cases_t_minus_7 = np.pad(cases_array[:-7], (7, 0), constant_values=0)

rt_proxy = np.divide(
    cases_array, 
    cases_t_minus_7, 
    out=np.zeros_like(cases_array, dtype=float), 
    where=cases_t_minus_7 != 0
)

national_df['rt_proxy'] = rt_proxy

plt.style.use('ggplot')
fig, axes = plt.subplots(3, 1, figsize=(12, 18))
plt.subplots_adjust(hspace=0.4)

april_onwards = national_df[national_df['date'] >= '2026-04-01']
axes[0].bar(april_onwards['date'], april_onwards['new_cases'], color='darkred', alpha=0.8)
axes[0].set_title('Epidemic Curve: Daily New Cases (Since April 2026)', fontsize=14, fontweight='bold')
axes[0].set_ylabel('New Confirmed Cases')
axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

zone_totals = df.groupby('health_zone')['confirmed_cases'].max().sort_values(ascending=True)
zone_totals.tail(15).plot(kind='barh', ax=axes[1], color='coral')
axes[1].set_title('Health-Zone Breakdown: Top 15 Most Affected Zones', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Cumulative Confirmed Cases')
axes[1].set_ylabel('Health Zone')

national_cum = df.groupby('date')[['confirmed_cases', 'deaths']].sum().reset_index()
national_cum['cfr'] = np.where(
    national_cum['confirmed_cases'] > 0, 
    (national_cum['deaths'] / national_cum['confirmed_cases']) * 100, 
    0
)

axes[2].plot(national_cum['date'], national_cum['cfr'], color='black', linewidth=2.5)
axes[2].set_title('Case-Fatality Ratio (CFR) Trend Over Time', fontsize=14, fontweight='bold')
axes[2].set_ylabel('CFR (%)')
axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

os.makedirs("dashboard", exist_ok=True)
plt.savefig("dashboard/epidemic_insights.png")
print("Processing complete. Insights plotted and saved to dashboard/epidemic_insights.png")