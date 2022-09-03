import sqlite3
import streamlit as st
from objects import Team
import game_functions
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np

# basic function we may use later
def flatten_2d_list(the_list):
    flat_list = []
    for sublist in the_list:
        for thing in sublist:
            flat_list.append(thing)
    return flat_list

# title and stuff
st.set_page_config(page_title = 'Ball.Sim (Beta)', page_icon = '⚾️')
st.title('Ball.Sim (Beta)')
st.write('\nCreated by Jensen Holm')
st.write('Data Source: [Sports-Reference](https://sports-reference.com)')
st.write('\n[Donate](https://www.paypal.com/donate/?business=HPLUVQJA6GFMN&no_recurring=0&currency_code=USD)')

# option menu (want to change icons somehow)
selected_page = option_menu(menu_title = None, options = ["Main", "Docs"], orientation = 'horizontal', icons = ['house', 'gear'])

# get rid of streamlit option menu stuff
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

# import the player data dict dictionaries for the keys so we can have options in the select box
sim_data_db = sqlite3.connect("Sim_Data.db")

# get list of all table names with the cursor to put into the st.select_box
all_teams_array = np.array(pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", sim_data_db))

# the all teams array is nested so lets unnest it
all_teams_with_year = flatten_2d_list(all_teams_array)

all_teams = [team[len('Year '):] for team in all_teams_with_year if "1972" not in team]
all_teams.sort(reverse = True)
all_teams.insert(0, "Start typing and select team")

# user unput buttons and sliders
if selected_page == "Main":
    st.text("\n(Currently teams 1973 through 2021 are available, rest in progress.)")
    team1 = st.selectbox(label = "Team 1", options = all_teams)
    team2 = st.selectbox(label = "Team 2", options = all_teams)

    number_of_simulations = st.slider("Number of Simulations", min_value = 162, max_value = 1620, step = 162)

# initialize simulation button
init_button = st.button("Go", help = "Begin Simulation")
if init_button:
    # potential errors
    if selected_page == "Docs":
        st.error("Cannot initialize simulation from 'Docs' page.")
        st.stop()

    if team1 == "Start typing and select team" or team2 == "Start typing and select team":
        st.error("Must select team from select boxes.")
        st.stop()

    # select databse tables based on user input
    team1_data = pd.read_sql_query(f"SELECT * FROM 'Year {team1}'", con = sim_data_db)
    team2_data = pd.read_sql_query(f"SELECT * FROM 'Year {team2}'", con = sim_data_db)

    team1_year = team1[:5]
    team2_year = team1[:5]
    team1_name = team1[5:]
    team2_name = team2[5:]

    # generate teams with the data queried above
    Team1 = Team(team1_name, team1_year, team1_data, lineup_settings = 'auto')
    Team2 = Team(team2_name, team2_year, team2_data, lineup_settings = 'auto')

    # begin simulation
    pbp_df, wins_time_df = game_functions.simulation(number_of_simulations, Team1, Team2, 0)

    # display records
    col1, col2 = st.columns(2)
    col1.metric(f"{Team1.name} win %", f"{100 * (Team1.wins / number_of_simulations):.3f}%")
    col2.metric(f"{Team2.name} win %", f"{100 * (Team2.wins / number_of_simulations):.3f}%")

    # display runs per game
    col1, col2 = st.columns(2)
    col1.metric(f"{Team1.name} Runs / Game", f"{Team1.runs / number_of_simulations:.2f}")
    col2.metric(f"{Team2.name} Runs / Game", f"{Team2.runs / number_of_simulations:.2f}")

    st.header("Wins / Time")
    st.line_chart(data = wins_time_df)

    # stats expanders
    st.header("Batting Stats")
    with st.expander(f"{team1_name} Individual Batting Stats"):
        for hitter in Team1.lineup:
            hitter.display_rate_stats()

    with st.expander(f"{team2_name} Individual Batting Stats"):
        for hitter in Team2.lineup:
            hitter.display_rate_stats()

    st.header("Pitching Stats")
    with st.expander(f"{team1_name} Individual Pitching Stats"):
        for pitcher in Team1.rotation:
            pitcher.display_rate_stats()
    
    with st.expander(f"{team2_name} Individual Pithcing Stats"):
        for pitcher in Team2.rotation:
            pitcher.display_rate_stats()


    # make it a csv and use st.download_button()
#     pbp_csv = convert_df(pbp_df)
#     st.download_button("Download Play By Play Data", pbp_csv, file_name = "BallSimPBP.csv")

    # use st.tabs to filter what to see, like a chart tab for the graph, a place where they can view stats per 162 for each player
    # and download data and stuff on another one (may need to figure out the st.session state thing tho)


# footer type stuff, plugging myself.
st.text('\n\n\n\n\n\n\n\n\n')
st.write(f'\n\nFeedback and report bugs: holmj@mail.gvsu.edu')
st.write('\nSocials: [Twitter](https://twitter.com/JensenH_) [GitHub](https://github.com/Jensen-holm) [Linkedin](https://www.linkedin.com/in/jensen-holm-3584981bb/)')
st.write('[Documentation / Code](https://github.com/Jensen-holm/MLB-APP)')
