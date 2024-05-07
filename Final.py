import pandas as pd 
import plotly.graph_objs as go
import streamlit as st

pd.set_option('display.max_columns', None)

##--------------------------------------------------------------------------------------------

def load_data(csv):
    df = pd.read_csv(csv)
    return df

df = load_data('Data/gun-violence-data_01-2013_03-2018.csv')

df['date']=pd.to_datetime(df['date'])
df['year']=df['date'].dt.year
df['month'] = df['date'].dt.month

def count_genders(gender_str):
    genders = gender_str.split('||')
    male_count = 0
    female_count = 0
    for g in genders:
        if '::Male' in g:
            male_count += 1
        elif '::Female' in g:
            female_count += 1
    return male_count, female_count

gender_counts = df['participant_gender'].fillna('').apply(count_genders)
total_male_count = sum(count[0] for count in gender_counts)
total_female_count = sum(count[1] for count in gender_counts)

print("Total Male Count:", total_male_count)
print("Total Female Count:", total_female_count)

def separate(df):
    df=df.split("||")
    df=[(x.split("::")) for x in df]
    y = []
    for  i in range (0, len(df)):
        y.append(df[i][-1])
    return(y) 

df['participant_gender'] = df['participant_gender'].fillna("0::Zero")
df['gender'] = df['participant_gender'].apply(lambda x: separate(x))
df['Males'] = df['gender'].apply(lambda x: x.count('Male'))
df['Females'] = df['gender'].apply(lambda x: x.count('Female'))

state_groups = df.groupby('state')

statesdf = state_groups.agg(
    total=('state', 'count'),  
    killed=('n_killed', 'sum'),  
    injured=('n_injured', 'sum'),  
    males=('Males', 'sum'),
    females=('Females', 'sum'),
)

statesdf = statesdf.reset_index()

state_to_code = {'District of Columbia' : 'DC','Mississippi': 'MS', 'Oklahoma': 'OK', 'Delaware': 'DE', 'Minnesota': 'MN', 'Illinois': 'IL', 'Arkansas': 'AR', 'New Mexico': 'NM', 'Indiana': 'IN', 'Maryland': 'MD', 'Louisiana': 'LA', 'Idaho': 'ID', 'Wyoming': 'WY', 'Tennessee': 'TN', 'Arizona': 'AZ', 'Iowa': 'IA', 'Michigan': 'MI', 'Kansas': 'KS', 'Utah': 'UT', 'Virginia': 'VA', 'Oregon': 'OR', 'Connecticut': 'CT', 'Montana': 'MT', 'California': 'CA', 'Massachusetts': 'MA', 'West Virginia': 'WV', 'South Carolina': 'SC', 'New Hampshire': 'NH', 'Wisconsin': 'WI', 'Vermont': 'VT', 'Georgia': 'GA', 'North Dakota': 'ND', 'Pennsylvania': 'PA', 'Florida': 'FL', 'Alaska': 'AK', 'Kentucky': 'KY', 'Hawaii': 'HI', 'Nebraska': 'NE', 'Missouri': 'MO', 'Ohio': 'OH', 'Alabama': 'AL', 'Rhode Island': 'RI', 'South Dakota': 'SD', 'Colorado': 'CO', 'New Jersey': 'NJ', 'Washington': 'WA', 'North Carolina': 'NC', 'New York': 'NY', 'Texas': 'TX', 'Nevada': 'NV', 'Maine': 'ME'}
statesdf['state_code'] = statesdf['state'].apply(lambda x : state_to_code[x])

state_year_groups = df.groupby(['state', 'year'])
state_year_counts = state_year_groups.size().reset_index(name='year_count')
statesdf = statesdf.merge(state_year_counts, on=['state'], how='left')
statesdf['year_count'] = statesdf['year_count'].fillna(0).astype(int)

statesdf = statesdf[(statesdf['year'] != 2013) & (statesdf['year'] != 2018)]

##--------------------------------------------------------------------------------------------

st.title('Gun Violence Incidents Visualization')

# Get unique years and add a "Total" option
year_options = sorted(statesdf['year'].unique())
year_options.insert(0, "Total")  

selected_year = st.selectbox("Select Year:", year_options)

if selected_year == "Total":
  map_data = {
    "locations": statesdf['state_code'].tolist(),
    "z": statesdf['total'].astype(int).tolist(),
  }
  totalfig = go.Figure(data=go.Choropleth(
      locations=statesdf['state_code'], 
      z = statesdf['total'], 
      locationmode = 'USA-states', 
      colorscale = 'Ylorrd',
      colorbar_title = "Thousands",
  ))
  totalfig.update_layout(
      title_text = 'Gun Violence incidents by State',
      geo = dict(
          scope='usa',
          projection=go.layout.geo.Projection(type = 'albers usa'),
          showlakes=True, 
          lakecolor='rgb(137, 207, 240)',),
  )
else:
  year_specific_df = statesdf.loc[statesdf['year'] == int(selected_year)]
  
  map_data = {
    "locations": year_specific_df['state_code'].tolist(),
    "z": year_specific_df['year_count'].astype(int).tolist(),
  }
  totalfig = go.Figure(data=go.Choropleth(
    locations=map_data['locations'], 
    z = map_data['z'], 
    locationmode = 'USA-states', 
    colorscale = 'Ylorrd',
    colorbar_title = "Thousands",
  ))
  totalfig.update_layout(
      title_text = 'Gun Violence incidents by State',
      geo = dict(
          scope='usa',
          projection=go.layout.geo.Projection(type = 'albers usa'),
          showlakes=True, # lakes
          lakecolor='rgb(137, 207, 240)',),
  )

st.plotly_chart(totalfig)

##--------------------------------------------------------------------------------------------
st.write('--------------------------------------------------------------------------------------------')

st.subheader('Year to year')

year_groups = df.groupby('year')

killed_counts = year_groups['n_killed'].sum()
injured_counts = year_groups['n_injured'].sum()

year_data = pd.DataFrame({'year': killed_counts.index, 'killed': killed_counts.values, 'injured': injured_counts.values})
year_data = year_data[(year_data['year'] != 2013) & (year_data['year'] != 2018)]

if not year_data.empty:  
    st.bar_chart(year_data, x='year', y=['killed', 'injured'])
else:
    st.write("No data available for the selected year.")

##--------------------------------------------------------------------------------------------
st.write('--------------------------------------------------------------------------------------------')

st.subheader('Age Totals')

df['participant_age_group'] = df['participant_age_group'].fillna("0::Zero")
df['Age'] = df['participant_age_group'].apply(lambda x: separate(x))
df['Child 0-11'] = df['Age'].apply(lambda x: x.count('Child 0-11'))
df['Teen 12-17'] = df['Age'].apply(lambda x: x.count('Teen 12-17'))
df['Adult 18+'] = df['Age'].apply(lambda x: x.count('Adult 18+'))

df = df[(df['year'] != 2013) & (df['year'] != 2018)]

colors = {
    'Child 0-11': 'blue',
    'Teen 12-17': 'green',
    'Adult 18+': 'red'
}

age_group = df[['year', 'Child 0-11', 'Teen 12-17', 'Adult 18+']].groupby('year').sum()
age_group['Total'] = age_group.sum(axis=1)

age_year_options = sorted(df['year'].unique())
age_year_options.insert(0, "Total")  # Insert "Total" at the beginning

selected_year = st.selectbox("Select Year", age_year_options)
if selected_year == "Total":
    traces = []
    for column in age_group.columns[:-1]:  # Exclude the 'Total' column
        trace = go.Scatter(x=age_group.index, y=age_group[column], mode='lines+markers', name=column,
                           line=dict(color=colors.get(column, 'gray')))  # Use a default color if not found
        traces.append(trace)

    layout = go.Layout(title=f'Gun Violence Incidents by Age Group for All Years',
                       xaxis=dict(title='Year'),
                       yaxis=dict(title='Counts'))

    fig = go.Figure(data=traces, layout=layout)

    st.plotly_chart(fig)
elif selected_year:
    
    selected_data = df[df['year'] == selected_year]
    selected_age_group = selected_data[['month', 'Child 0-11', 'Teen 12-17', 'Adult 18+']].groupby('month').sum()
    selected_age_group['Total'] = selected_age_group.sum(axis=1)

    selected_traces = []
    for column in selected_age_group.columns[:-1]:  # Exclude the 'Total' column
        selected_trace = go.Scatter(x=selected_age_group.index, y=selected_age_group[column], mode='lines+markers', name=column,
                                    line=dict(color=colors.get(column, 'gray')))  # Use a default color if not found
        selected_traces.append(selected_trace)

    selected_layout = go.Layout(title=f'Gun Violence Incidents by Age Group for {selected_year}',
                                xaxis=dict(title='Month'),
                                yaxis=dict(title='Counts'))

    selected_fig = go.Figure(data=selected_traces, layout=selected_layout)

    st.plotly_chart(selected_fig)

    st.write('--------------------------------------------------------------------------------------------')

def count_individual_incidents(incident_str):
    if isinstance(incident_str, str):  
        incidents = incident_str.split('||')
        incident_counts = {}
        for incident_entry in incidents:
            if incident_entry in incident_counts:
                incident_counts[incident_entry] += 1
            else:
                incident_counts[incident_entry] = 1
        return incident_counts
    else:
        return {}

total_incident_counts = {}

for entry in df['incident_characteristics']:
    individual_incident_counts = count_individual_incidents(entry)
    for incident, count in individual_incident_counts.items():
        if incident in total_incident_counts:
            total_incident_counts[incident] += count
        else:
            total_incident_counts[incident] = count

sorted_incident_counts = sorted(total_incident_counts.items(), key=lambda x: x[1], reverse=True)

st.subheader("Top 5 most common incidents:")
for i, (incident, count) in enumerate(sorted_incident_counts[:5], 1):
    st.write(f"{i}. {incident}: {count} occurrences")
