# Sam Carlson
# Ryan Alian

# Cameron Ahn
# Colin Braddy
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import datetime as dt 
from vega_datasets import data

#Get Recorded US deaths csv from Official Github and return as Pandas dataframe
st.set_page_config(layout="wide")
@st.cache
def load_raw_deaths_csv():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
    df = pd.read_csv(url)
    return df

#Get Recorded US cases csv from Official Github and return as Pandas dataframe
@st.cache
def load_raw_cases_csv():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
    df = pd.read_csv(url)
    #df.to_csv("covid_cases.csv")
    return df

# This method returns a dataframe which columns with no recorded deaths in any state are dropped.
def stateDeathsOverTime(raw):
    # Drop arbitrary columns (We can't .copy columns because each indivudal date is a column)
    rawdf = raw.drop(['UID','iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Lat', 'Long_', 'Combined_Key', 'Country_Region', 'Population'], 1)
    # At this point we have a Dataframe of deaths in the United States per County per State.
    # Sum county deaths to confine deaths to indivual States
    rawdf  = rawdf.reset_index().groupby(['Province_State']).sum()
    # Deaths are recorded as a cumulative total. Not each day.
    # So, Some Columns are sum = 0, Remove these to remove eventless days.
    deathsOvertime = rawdf.loc[(rawdf.sum(axis=1) != 0), (rawdf.sum(axis=0) != 0)]
    deathsOvertime = deathsOvertime.drop(['index'], 1)
    return deathsOvertime

#This method starts by getting the dataframe with only columns containing deaths in them (From stateDeathOT()) and summing each row.
def stateDeathTotal(raw):
    # Remove useless columns and condense to only days with recorded deaths
    rawdf = stateDeathsOverTime(raw)
    # We need to access the most recent data entry (Last column) which will provide us total deaths per state
    rawdf["Deaths"] = rawdf.iloc[:,-1:]
    # Now we can create a Dataframe with only the states and their cumulative deaths (dfStateDeaths)
    dfStateDeaths = rawdf[["Deaths"]].copy()
    dfStateDeaths = pd.merge(dfStateDeaths, stateIDs(), on='Province_State')
    return dfStateDeaths

def stateIDs():
    #In order to properly present this visually we need to assign StateIDs to their respective states.
    #! import previously used .csv from another project to get State IDS (We need to replace this if we can)
    df2 = pd.read_csv('https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/population_engineers_hurricanes.csv')
    stateID = df2[["state","id"]].copy()
    stateID.columns = ['Province_State', 'id']
    stateID.set_index('Province_State')
    return stateID


def stateDeathsChart():
    df = stateDeathsOverTime(load_raw_deaths_csv())
    df = df.drop(['American Samoa'], 0)
    df = pd.melt(df, ignore_index=False)
    df['variable'] = pd.to_datetime(df.variable)
    df = df.sort_values(by=['Province_State', 'value'])
    df = df.reset_index('Province_State')
    return df

# returns a dataframe which columns with no recorded cases in any state are dropped
def stateCasesOverTime(raw): 
    # drop arbitrary columns
    rawdf = raw.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2','Country_Region', 'Lat', 'Long_', 'Combined_Key'], 1) 
    # sums county cases to provide cases per territory
    rawdf  = rawdf.reset_index().groupby(['Province_State']).sum()
    #Cases are recorded as a cumulative total. Not per day
    #Some Columns are sum = 0, Remove these
    casesOvertime = rawdf.loc[(rawdf.sum(axis=1) != 0), (rawdf.sum(axis=0) != 0)]
    casesOvertime = casesOvertime.drop(['index'], 1)
    return casesOvertime

# Gets the dataframe with only columns containing deaths in them (From stateCasesOT()) and summing each row
def stateCaseTotal(raw): 
    rawdf = stateCasesOverTime(raw)
    #We need to access the most recent data entry (Last column) which will provide us total cases per state
    rawdf["Cases"] = rawdf.iloc[:,-1:]
    #Now we can create a Dataframe with only the states and their cumulative cases (dfStateCases)
    dfStateCases = rawdf[["Cases"]].copy()
    dfStateCases = pd.merge(dfStateCases, stateIDs(), on='Province_State')
    return dfStateCases

# converts dataframe containing state cases over time into a format compatible for use in line chart
def stateCaseChart():
    df = stateCasesOverTime(load_raw_cases_csv())
    df = df.drop(['American Samoa'], 0)
    df = pd.melt(df, ignore_index=False)
    df['variable'] = pd.to_datetime(df.variable)
    df = df.sort_values(by=['Province_State', 'value'])
    df = df.reset_index('Province_State')
    return df

# State death dataframe setup
rawDeathsdf = load_raw_deaths_csv()
dfStateDeathsOverTime = stateDeathsOverTime(rawDeathsdf)
dfStateTotalDeaths = stateDeathTotal(rawDeathsdf)
deathChartDf = stateDeathsChart()

# State case dataframe setup
raw_cases = load_raw_cases_csv()
dfStateCasesOverTime = stateCasesOverTime(raw_cases)
dfStateTotalCases = stateCaseTotal(raw_cases)
caseChartDf = stateCaseChart()

#Death to Cases Ratio dataframe setup
dfStateCaseDeathRatio = pd.merge(dfStateTotalDeaths, dfStateTotalCases.drop(['id'], 1), on='Province_State')
dfStateCaseDeathRatio['Ratio'] = dfStateCaseDeathRatio['Deaths']/dfStateCaseDeathRatio['Cases']

###CHARTS###
# Choropleth map for US deaths
usDeathMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Deaths:O'],
    color='Deaths:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalDeaths, 'id', ['Deaths'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Choropleth map for US cases
usCaseMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Cases:O'],
    color='Cases:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalCases, 'id', ['Cases'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

#Here is a barchart with Average Deaths comparing all States
avgDeaths = dfStateTotalDeaths["Deaths"].mean()
bar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x='Province_State:O',
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
sortedbar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x=alt.X('Province_State:O', sort='-y'),
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
rule = alt.Chart(dfStateTotalDeaths).mark_rule(color='red').encode(
    y='mean(Deaths):Q'
)
barChart = (bar + rule).properties(width=900, height = 500)
sortedbarChart = (sortedbar + rule).properties(width=900, height = 500)

#

highlight = alt.selection(type='single', on='mouseover',
                          fields=['Province_State'], nearest=True)

deathsAllStatesbase = alt.Chart(deathChartDf).mark_line().encode(
    #opacity=alt.value(0),
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

deathsAllStatespoints = deathsAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

deathsAllStateslines = deathsAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

deathsAllStates = deathsAllStatespoints + deathsAllStateslines

# Line chart
# Line chart base - ask team members about. Why do the base, points, and lines of the chart have to be created separately
casesAllStatesbase = alt.Chart(caseChartDf).mark_line().encode(
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

# Line chart points 
casesAllStatespoints = casesAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

casesAllStateslines = casesAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

# Line chart - why do the points and lines have to be created separately, then combined?
casesAllStates = casesAllStatespoints + casesAllStateslines

#########

###CHARTS###
# Choropleth map for US deaths
usDeathMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Deaths:O'],
    color='Deaths:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalDeaths, 'id', ['Deaths'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Choropleth map for US cases
usCaseMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Cases:O'],
    color='Cases:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalCases, 'id', ['Cases'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

#Here is a barchart with Average Deaths comparing all States
avgDeaths = dfStateTotalDeaths["Deaths"].mean()
bar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x='Province_State:O',
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
sortedbar = alt.Chart(dfStateTotalDeaths).mark_bar().encode(
    x=alt.X('Province_State:O', sort='-y'),
    y='Deaths:Q',
    color=alt.condition(
        alt.datum.Deaths > avgDeaths, 
        alt.value('orange'),
        alt.value('steelblue')
    )
)
rule = alt.Chart(dfStateTotalDeaths).mark_rule(color='red').encode(
    y='mean(Deaths):Q'
)
barChart = (bar + rule).properties(width=900, height = 500)
sortedbarChart = (sortedbar + rule).properties(width=900, height = 500)


avgCases = dfStateTotalCases["Cases"].mean()
bar_case = alt.Chart(dfStateTotalCases).mark_bar().encode(
    x='Province_State:O',
    y='Cases:Q',
    color=alt.condition(
        alt.datum.Cases > avgCases,
        alt.value('orange'),
        alt.value('steelblue')
    )
)

sortedbar_case = alt.Chart(dfStateTotalCases).mark_bar().encode(
    x=alt.X('Province_State:O', sort='-y'),
    y='Cases:Q',
    color=alt.condition(
        alt.datum.Cases > avgCases,
        alt.value('orange'),
        alt.value('steelblue')
    )
)

rule_case = alt.Chart(dfStateTotalCases).mark_rule(color='red').encode(
    y='mean(Cases):Q'
)

barChart_case = (bar_case + rule_case).properties(width=900, height=500)
sortedbarChart_case = (sortedbar_case + rule_case).properties(width=900, height=500)
#

highlight = alt.selection(type='single', on='mouseover',
                          fields=['Province_State'], nearest=True)

deathsAllStatesbase = alt.Chart(deathChartDf).mark_line().encode(
    #opacity=alt.value(0),
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

deathsAllStatespoints = deathsAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

deathsAllStateslines = deathsAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

deathsAllStates = deathsAllStatespoints + deathsAllStateslines

# Line chart
# Line chart base - ask team members about. Why do the base, points, and lines of the chart have to be created separately
casesAllStatesbase = alt.Chart(caseChartDf).mark_line().encode(
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value"]
)

# Line chart points 
casesAllStatespoints = casesAllStatesbase.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
).properties(
    width=900,
    height=1000
)

casesAllStateslines = casesAllStatesbase.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
)

# Line chart - why do the points and lines have to be created separately, then combined?
casesAllStates = casesAllStatespoints + casesAllStateslines


# Deaths to Cases Ratio Graphs
# Choropleth map for US Deaths to Cases Ratio
usCaseDeathRatioMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Ratio:O'],
    color='Ratio:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateCaseDeathRatio, 'id', ['Ratio'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)



########################
# Streamlit App Layout #
########################

st.title('COVID Data')
st.header("Visual Analytics Project | Team 7");
st.write("Cameron Ahn, Ryan Alian, Colin Braddy, Sam Carlson")

allStates = dfStateTotalDeaths['Province_State'].values.tolist()
statesSelected = st.multiselect('What States do you want to compare?', allStates, allStates[0])

deathCol, caseCol = st.beta_columns(2)
#caseCol, deathCol = st.beta_columns(2)


#Column for Death stats
deathCol.header("Recorded Deaths in the United States")

if deathCol.checkbox('View Original Dataframe:'):
    deathCol.header("Dataframe of State Cumulative Deaths from COVID-19: ")
    deathCol.dataframe(rawDeathsdf)
if deathCol.checkbox('View Simplified Dataframe:'):
    deathCol.header("Dataframe of States/Total Deaths from COVID-19: ")
    deathCol.dataframe(dfStateTotalDeaths)
        
deathCol.subheader("Deaths from COVID-19 across the United States: ")
deathCol.write(usDeathMap)
    
deathCol.subheader("Chart of States/Deaths (Highlighted is above the National Average)")
if deathCol.checkbox('Sort by Most to Least Deaths'):
    deathCol.write(sortedbarChart)
else:
    deathCol.write(barChart)
    
deathCol.subheader("Graph of death trends for each State: ")
deathCol.write(deathsAllStates)

    
#Column for Death stats
caseCol.header("Recorded Cases in the United States")

if caseCol.checkbox('View Original Cases Dataframe:'):
    caseCol.header("Dataframe of State Cumulative Cases from COVID-19: ")
    caseCol.dataframe(raw_cases)
if caseCol.checkbox('View Simplified Cases Dataframe:'):
    caseCol.header("Dataframe of States/Total Cases from COVID-19: ")
    caseCol.dataframe(dfStateTotalCases)
    
caseCol.subheader("Confirmed Cases of COVID-19 Across the United States: ")
caseCol.write(usCaseMap)

caseCol.subheader("Chart of States/Cases (Highlighted is above the National Average)")
if caseCol.checkbox('Sort by Most to Least Cases'):
    caseCol.write(sortedbarChart_case)
else:
    caseCol.write(barChart_case)
    
caseCol.subheader("Graph of Case trends for each State: ")
caseCol.write(casesAllStates)
    

st.subheader('Ratio of Deaths to Cases in the United States')
st.write(usCaseDeathRatioMap)

#
#if st.sidebar.checkbox('Show Raw Death Data'):
#    st.write("Raw COVID Death data from Github: ")
#    st.dataframe(raw)
#    
#if st.sidebar.checkbox('Show Raw Case Data'):
#    st.write("Raw COVID Case data from Github: ")
#    st.dataframe(raw_cases)

