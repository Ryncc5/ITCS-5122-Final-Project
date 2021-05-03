# Sam Carlson
# Ryan Alian

# Cameron Ahn
# Colin Braddy
import streamlit as st
import altair as alt
import pandas as pd
import time
import numpy as np
import datetime
from vega_datasets import data
from datetime import date,time


#Get Recorded US deaths csv from Official Github and return as Pandas dataframe
st.set_page_config(layout="wide")
@st.cache
def load_raw_deaths_csv():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
    df = pd.read_csv(url)
    df.to_csv("covid_deaths.csv")
    return df

#Get Recorded US cases csv from Official Github and return as Pandas dataframe
@st.cache
def load_raw_cases_csv():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
    df = pd.read_csv(url)
    df.to_csv("covid_cases.csv")
    return df

#Get Recorded World deaths csv from Official Github and return as Pandas dataframe
@st.cache
def load_raw_csv_global():
    url2 = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
    df2 = pd.read_csv(url2)
    df2.to_csv("world_deaths.csv")
    return df2

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


def stateDeathsChart(raw):
    #raw = raw.drop(['American Samoa'], 0)
    raw = pd.melt(raw, ignore_index=False)
    raw['variable'] = pd.to_datetime(raw.variable)
    raw = raw.sort_values(by=['Province_State', 'value'])
    raw = raw.reset_index('Province_State')
    return raw

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
def stateCaseChart(raw):
    #df = df.drop(['American Samoa'], 0)
    raw = pd.melt(raw, ignore_index=False)
    raw['variable'] = pd.to_datetime(raw.variable)
    raw = raw.sort_values(by=['Province_State', 'value'])
    raw = raw.reset_index('Province_State')
    return raw

def userSelectedStateDeaths(selected):
    deathsDf = stateDeathsOverTime(rawDeathsdf)
    selectedDf = deathsDf.loc[selected].copy()
    return selectedDf

def userSelectedStateCases(selected):
    casesDf = stateCasesOverTime(raw_cases)
    selectedDf = casesDf.loc[selected].copy()
    return selectedDf

# This method returns a dataframe which columns with no recorded deaths in any state are dropped.
def countryDeathsOverTime(globalRaw):
    # Drop arbitrary columns
    rawdf = globalRaw.drop(
        ['Lat', 'Long'], 1)
    # At this point we have a Dataframe of deaths for each country.
    # Sum deaths to provide deaths per country/region
    rawdf = rawdf.reset_index().groupby(['Country/Region']).sum()
    # Deaths are recorded as a cumulative total. Not per day
    # Some Columns are sum = 0, Remove these
    countryDeathsOvertime = rawdf.loc[(rawdf.sum(axis=1) != 0), (rawdf.sum(axis=0) != 0)]
    countryDeathsOvertime = countryDeathsOvertime.drop(['index'], 1)
    return countryDeathsOvertime


# This method starts by getting the dataframe with only columns containing deaths in them (From countryDeathOT()) and summing each row.
def countryDeathTotal(globalRaw):
    rawdf = countryDeathsOverTime(globalRaw)
    # We need to access the most recent data entry (Last column) which will provide us total deaths per country
    rawdf["Deaths"] = rawdf.iloc[:, -1:]
    # Now we can create a Dataframe with only the countries and their cumulative deaths (dfCountryDeaths)
    dfCountryDeaths = rawdf[["Deaths"]].copy()
    return dfCountryDeaths


def countryDeathsChart():
    df = countryDeathsOverTime(load_raw_csv_global())
    df = pd.melt(dfCountryDeathsOT, ignore_index=False)
    df['variable'] = pd.to_datetime(df.variable)
    df = df.sort_values(by=['Country/Region', 'value'])
    df = df.reset_index('Country/Region')
    return df

##############################
### Data Setup/Manipulation ##
##############################


# State death dataframe setup
rawDeathsdf = load_raw_deaths_csv()
dfStateDeathsOverTime = stateDeathsOverTime(rawDeathsdf)
dfStateTotalDeaths = stateDeathTotal(rawDeathsdf)
deathChartDf = stateDeathsChart(dfStateDeathsOverTime)

# State case dataframe setup
raw_cases = load_raw_cases_csv()
dfStateCasesOverTime = stateCasesOverTime(raw_cases)
dfStateTotalCases = stateCaseTotal(raw_cases)
caseChartDf = stateCaseChart(dfStateCasesOverTime)

#Death to Cases Ratio dataframe setup
dfStateCaseDeathRatio = pd.merge(dfStateTotalDeaths, dfStateTotalCases.drop(['id'], 1), on='Province_State')
dfStateCaseDeathRatio['Ratio'] = dfStateCaseDeathRatio['Deaths']/dfStateCaseDeathRatio['Cases']

#World death data setup
globalRaw = load_raw_csv_global()
dfCountryDeathsOT = countryDeathsOverTime(globalRaw)
dfCountryTotalDeaths = countryDeathTotal(globalRaw)
countryDeathsChart = countryDeathsChart()

dfCountryLatLong = globalRaw.filter(['Country/Region','Lat','Long'], axis=1)
dfCountryTotalDeaths = dfCountryTotalDeaths.reset_index()
dfCountryLatLong['Deaths'] = dfCountryTotalDeaths['Deaths'].copy()

#State Population versus Cases/Deaths Setup
dfStatePopulation = rawDeathsdf.filter(['Province_State', 'Population'], axis=1)
# Sum populations State
dfStatePopulation = dfStatePopulation.groupby(['Province_State']).sum()
dfStatePopulation = dfStatePopulation.reset_index()

dfStatePopulationDeathRatio = pd.merge(dfStateTotalDeaths, dfStatePopulation, on='Province_State')
dfStatePopulationCasesRatio = pd.merge(dfStateTotalCases, dfStatePopulation, on='Province_State')

dfStatePopulationDeathRatio['Ratio'] = dfStatePopulationDeathRatio['Deaths']/dfStatePopulationDeathRatio['Population']
dfStatePopulationCasesRatio['Ratio'] = dfStatePopulationCasesRatio['Cases']/dfStatePopulationCasesRatio['Population']

########################
############## CHARTS ##
########################

# Choropleth map for US deaths
usDeathMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Province_State:N','Deaths:O'],
    color='Deaths:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalDeaths, 'id', ['Deaths', 'Province_State'] )
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Choropleth map for US cases
usCaseMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Province_State:N', 'Cases:O'],
    color='Cases:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateTotalCases, 'id', ['Cases','Province_State'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Choropleth map for US Deaths to Cases Ratio
usCaseDeathRatioMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Province_State:N','Ratio:O'],
    color=alt.Color('Ratio:Q', legend=alt.Legend(format=".0%"))
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStateCaseDeathRatio, 'id', ['Ratio','Province_State'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)
# Choropleth map for US Deaths/Population Ratio
usDeathPopulationMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Province_State:N','Ratio:O'],
    color=alt.Color('Ratio:Q', legend=alt.Legend(format=".00%"))
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStatePopulationDeathRatio, 'id', ['Ratio','Province_State'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)
# Choropleth map for US Cases/Population Ratio
usCasePopulationMap = alt.Chart(alt.topo_feature(data.us_10m.url, 'states')).mark_geoshape().encode(
    tooltip=['Province_State:N','Ratio:O'],
    color=alt.Color('Ratio:Q', legend=alt.Legend(format=".00%"))
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dfStatePopulationCasesRatio, 'id', ['Ratio','Province_State'])
).project(
    type='albersUsa'
).properties(
    width=900,
    height=500
)

# Here is a barchart with Average Deaths comparing all States
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
# Here is a barchart with Average Deaths comparing all States sorted by most to least
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

# Here is a barchart with recorded Cases comparing all States average
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
# Here is a barchart with recorded Cases comparing all States average sorted by most to least
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

# This is the multiline graph which displays deaths over time for every state
highlight = alt.selection(type='single', on='mouseover',
                          fields=['Province_State'], nearest=True)

deathsAllStatesbase = alt.Chart(deathChartDf).mark_line().encode(
    #opacity=alt.value(0),
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value", "variable"]
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

# This is the multiline graph which displays cases over time for every state
casesAllStatesbase = alt.Chart(caseChartDf).mark_line().encode(
    x='variable',
    y='value',
    color='Province_State:N',
    tooltip=["Province_State:N", "value", "variable"]
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

#WORLD MAP
# worldDeathMap + pois need to be together to present to world data
worldDeathMap = alt.Chart(alt.topo_feature(data.world_110m.url, "countries")).mark_geoshape(
        fill='#ddd', stroke='#fff', strokeWidth=1.5
    ).project(
        type='equirectangular'
    ).properties(
        width=1000,
        height=500
    )
pois = alt.Chart(dfCountryLatLong).mark_circle().encode(
    latitude='Lat:Q',
    longitude='Long:Q',
    tooltip=["Country/Region:N", "Deaths"],
    size="Deaths"
)

####################################
############# Streamlit App Layout #
####################################

st.title('COVID Data')
st.header("Visual Analytics Project | Team 7");
st.write("Cameron Ahn, Ryan Alian, Colin Braddy, Sam Carlson")

allStates = dfStateTotalDeaths['Province_State'].values.tolist()

deathCol, caseCol = st.beta_columns(2)
#caseCol, deathCol = st.beta_columns(2)

with st.beta_expander('Select States to compare: '): 
    userSelectedStates = st.beta_container()
    statesSelected = userSelectedStates.multiselect('What States do you want to compare?', allStates, allStates[0])
    
    userSelectedStates.subheader("Date Range for data")
    startDate = userSelectedStates.date_input('Start Date', datetime.date(2020, 1, 22))
    endDate = userSelectedStates.date_input('End Date', datetime.date(2021, 5, 1))
    domain = [startDate.isoformat(), endDate.isoformat()]
    
    selectedStateDeaths = userSelectedStateDeaths(statesSelected)
    selectedStateCases = userSelectedStateCases(statesSelected)

    stateDeathsChart = stateDeathsChart(selectedStateDeaths)
    stateCaseChart = stateCaseChart(selectedStateCases)
    
    if userSelectedStates.checkbox('Compare Overall Deaths: '):
        selectedStateTotalDeaths = selectedStateDeaths.copy()
        selectedStateTotalDeaths = selectedStateTotalDeaths.reset_index()
        selectedStateTotalDeaths['Deaths'] = selectedStateTotalDeaths.iloc[:,-1:]

        #st.write('Overall Deaths for each selected State:')
        #st.write(selectedStateTotalDeaths)
        
        deathSelectBar = alt.Chart(selectedStateTotalDeaths).mark_bar().encode(
            x=alt.X('Province_State:O',title='State'),
            y=alt.Y('Deaths:Q',title='Total Deaths'),
            color= alt.value('steelblue'),
            tooltip=["Province_State:N", "Deaths:Q"]
        ).properties(
            width=700,
            height=700
        ).configure_axis(
            labelFontSize=20,
            titleFontSize=20
        )
        st.write(deathSelectBar)

    if userSelectedStates.checkbox('Compare Deaths Overtime: '):
        st.subheader('Deaths overtime for each State: ')
        selectDeathsLine = alt.Chart(stateDeathsChart).mark_line().encode(
            x=alt.X('variable',title='Date', scale=alt.Scale(domain=domain)),
            y=alt.Y('value', title='Total Deaths'),
            color='Province_State',
            tooltip=["Province_State:N", "value", "variable"]
        ).properties(
            width=900,
            height=1000
        ).interactive(
        ).configure_axis(
            labelFontSize=20,
            titleFontSize=20
        )
        st.write(selectDeathsLine)

    if userSelectedStates.checkbox('Compare Overall Cases: '):
        
        selectedStateTotalCases = selectedStateCases.copy()
        selectedStateTotalCases = selectedStateCases.reset_index()
        selectedStateTotalCases['Deaths'] = selectedStateTotalCases.iloc[:,-1:]

        #st.write('Overall Cases for each selected State:')
        #st.write(selectedStateTotalCases)

        deathSelectBar = alt.Chart(selectedStateTotalCases).mark_bar().encode(
            x=alt.X('Province_State:O', title='State'),
            y=alt.Y('Deaths:Q', title='Total Cases'),
            color= alt.value('steelblue'),
            tooltip=["Province_State:N", "Deaths:Q"]
        ).properties(
            width=700,
            height=700
        ).configure_axis(
            labelFontSize=20,
            titleFontSize=20
        )
        st.write(deathSelectBar)

    if userSelectedStates.checkbox('Compare Cases Overtime: '):
        st.subheader('Cases overtime for each State: ')
        selectCasesLine = alt.Chart(stateCaseChart).mark_line().encode(
            x=alt.X('variable', title='Date', scale=alt.Scale(domain=domain)),
            y=alt.Y('value', title='Total Cases'),
            color='Province_State',
            tooltip=["Province_State:N", "value", "variable"]
        ).properties(
            width=900,
            height=1000
        ).configure_axis(
            labelFontSize=20,
            titleFontSize=20
        ).interactive()
        st.write(selectCasesLine)
             
            
with st.beta_expander('US Data Insights'):
    #Container for Death to Case Ratio
    st.subheader('Ratio of Deaths per Cases Across the United States')
    ratioDeathCase = st.beta_container()
    ratioDeathCase.write(usCaseDeathRatioMap)
    
    st.subheader('Cases Percentage of State Population')
    st.write(usCasePopulationMap)
    
    st.subheader('Death Percentage of State Population')
    st.write(usDeathPopulationMap)
    
    
with st.beta_expander('US Case Data'):
    #Container for Case stats
    allCases = st.beta_container()
    allCases.header("Recorded Cases Across the United States")
    if allCases.checkbox('View Original Cases Dataframe:'):
        allCases.header("Dataframe of State Cumulative Cases from COVID-19: ")
        allCases.dataframe(raw_cases)
    if allCases.checkbox('View Simplified Cases Dataframe:'):
        allCases.header("Dataframe of States/Total Cases from COVID-19: ")
        allCases.dataframe(dfStateTotalCases)
        
    allCases.subheader("Confirmed Cases of COVID-19 Across the United States: ")
    allCases.write(usCaseMap)

    allCases.subheader("Chart of States/Cases (Highlighted is above the National Average)")
    if allCases.checkbox('Sort by Most to Least Cases'):
        allCases.write(sortedbarChart_case)
    else:
        allCases.write(barChart_case)

    allCases.subheader("Graph of Case trends for every State: ")
    allCases.write(casesAllStates)
    
with st.beta_expander('US Death Data'):
    #Container for death stats
    allDeaths = st.beta_container()
    allDeaths.header("Recorded Deaths in the United States")
    
    if allDeaths.checkbox('View Original Dataframe:'):
        allDeaths.header("Dataframe of State Cumulative Deaths from COVID-19: ")
        allDeaths.dataframe(rawDeathsdf)
    if allDeaths.checkbox('View Simplified Dataframe:'):
        allDeaths.header("Dataframe of States/Total Deaths from COVID-19: ")
        allDeaths.dataframe(dfStateTotalDeaths)
        
    allDeaths.subheader("Deaths from COVID-19 across the United States: ")
    allDeaths.write(usDeathMap)

    allDeaths.subheader("Chart of States/Deaths (Highlighted is above the National Average)")
    if allDeaths.checkbox('Sort by Most to Least Deaths'):
        allDeaths.write(sortedbarChart)
    else:
        allDeaths.write(barChart)

    allDeaths.subheader("Graph of Death trends for every State: ")
    allDeaths.write(deathsAllStates)
    
with st.beta_expander('Worldwide Data'):
    #Container for world statistics
    worldDeaths = st.beta_container()
    worldDeaths.write(worldDeathMap + pois)

with st.beta_expander('View Original Data Sources'):
    if st.checkbox('Show Raw Death Data'):
        st.write("Raw COVID Death data from Github: ")
        st.dataframe(load_raw_deaths_csv())

    if st.checkbox('Show Raw Case Data'):
        st.write("Raw COVID Case data from Github: ")
        st.dataframe(load_raw_cases_csv())
    
    if st.checkbox('Show World Death Data'):
        st.write("Raw Worldwide COVID Death data from Github: ")
        st.dataframe(load_raw_csv_global())
