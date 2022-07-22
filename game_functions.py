import streamlit as st
import random
import pandas as pd

""" Add per 162 game stats for each player for download """
''' first we should probably do session state tho '''

pbp_data = []
pbp_cols = ["Hitter Team", "Pitcher Team", "Hitter", "Pitcher", "PA Result",  "Game#", "Inning"]

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')

def determine_probs(hitter, pitcher):
    # if pitcher.throws == key, hit_probs == vlaue
    # for now if both we default to overall season probs for now
    hitter_probs_decision = {
        "Left":hitter.probsl,
        "Right":hitter.probsr,
        "Both":hitter.probsl # default to lefty probs if he's switch, fix later
    }

    pitcher_probs_decision = {
        "Left":pitcher.probsl,
        "Right":pitcher.probsr,
        "Both":pitcher.probsl # default to lefty probs if he is switch, work on this later
    }

    hit_probs = [value for key, value in hitter_probs_decision.items() if key == pitcher.throws]
    pit_probs = [value for key, value in pitcher_probs_decision.items() if key == hitter.bats]
    return hit_probs, pit_probs


def PA(hitter, pitcher, game_num, inning):

    # call previous determine probs function for readiblity when calling the PA function
    hit_probs, pit_probs = determine_probs(hitter, pitcher)
    outcome_dict = {}
    possible_outcomes = ['IPO', 'SO', 'BB', 'HBP', '1B', '2B', '3B', 'HR']
    # because hit probs and pit probs are nested
    for thing in hit_probs:
        for probh in thing:
            for thing2 in pit_probs:
                for probp in thing2:
                    if probh[0] == probp[0]:
                        if probh[0] and probp[0] in possible_outcomes:
                            outcome_dict[probh[0]] = (probh[1] + probp[1]) / 2
                            
    # decide outcome
    keys = [key for key in outcome_dict.keys() if key in possible_outcomes]
    probs = [value for key, value in outcome_dict.items() if key in possible_outcomes]
    outcome = random.choices(keys, probs)
    outs = 0
    if outcome[0] == "IPO":
        outs += 1
    elif outcome[0] == "SO":
        outs += 1

    hitter.PA += 1
    pitcher.BF += 1

    if outcome[0] not in ['BB', 'HBP']:
        hitter.AB += 1
    
    # make a dataframe of play by play data
    pbp_data.append([hitter.team, pitcher.team, hitter.name, pitcher.name,  outcome[0], game_num, inning])
    return outcome[0], outs


def clear_bases():
    return [None, None, None]


def check_bases_occupied(base_state):
    return sum([base_state.index(base) + 1 for base in base_state if base != None])



# run through this logic on paper and make sure it is sound...


# double check that this does what we want it to...

def advance_runners_on_hit(base_state, bases_advanced): # only really for singles and doubles
    runs_scored = 0
    for runner in base_state:
        if runner != None:
            new_index = base_state.index(runner) + bases_advanced
            if new_index < len(base_state):
                base_state[new_index] = runner
                base_state[new_index - 1] = None
            else:
                runs_scored += 1

    # move the runners up the number of bases_advanced up in the list,
    
    return runs_scored, base_state


def bb(hitter, pitcher, base_state):
    runs_scored = 0
    sum_bases = check_bases_occupied(base_state)
    # check for scenarios where a walk or hbp would move runners on
    if sum_bases == 1:
        base_state[1] = base_state[0]
        base_state[0] = hitter
    elif sum_bases == 6:
        base_state[2] = base_state[1]
        base_state[1] = base_state[0]
        base_state[0] = hitter
        runs_scored += 1
    else:
        base_state[0] == hitter
    hitter.BB += 1
    pitcher.BB += 1
    return runs_scored, base_state

def hbp(hitter, pitcher, base_state):
    runs_scored = 0
    sum_bases = check_bases_occupied(base_state)
    # check for scenarios where a walk or hbp would move runners on
    if sum_bases == 1:
        base_state[1] = base_state[0]
        base_state[0] = hitter
    elif sum_bases == 6:
        base_state[2] = base_state[1]
        base_state[1] = base_state[0]
        base_state[0] = hitter
        runs_scored += 1
    else:
        base_state[0] == hitter
    hitter.HBP += 1
    pitcher.HBP += 1
    return runs_scored, base_state



def IPO(hitter, pitcher, base_state):
    # eventually would like to make this include double play probability and players advancing on grounders and stuff eventually
    runs_scored = 0
    hitter.IPO += 1
    pitcher.IPO += 1
    return runs_scored, base_state


def K(hitter, pitcher, base_state):
    runs_scored = 0
    hitter.K += 1
    pitcher.K += 1
    return runs_scored, base_state


def single(hitter, pitcher, base_state):
    runs_scored = 0
    # move all runners one base
    runs, base_state = advance_runners_on_hit(base_state, 1)
    runs_scored += runs
    base_state[0] = hitter
    hitter.singles += 1
    pitcher.singles += 1
    hitter.H += 1
    hitter.TB += 1
    return runs_scored, base_state


def double(hitter, pitcher, base_state):
    # move all the base runners two spots up (nobody scores from first yet)
    runs_scored = 0
    runs, base_state = advance_runners_on_hit(base_state, 2)
    base_state[1] = hitter
    runs_scored += runs
    hitter.doubles += 1
    pitcher.doubles += 1
    hitter.H += 1
    hitter.TB += 2
    return runs_scored, base_state


def triple(hitter, pitcher, base_state):
    runs_scored = 0 
    runs_scored += len([base for base in base_state if base != None])
    base_state[2] = hitter
    hitter.triples += 1
    pitcher.triples += 1
    hitter.H += 1
    hitter.TB += 3
    return runs_scored, base_state


def homerun(hitter, pitcher, base_state):
    runs_scored = 0
    sum_bases = len([base for base in base_state if base != None])
    base_state = clear_bases()
    runs_scored += (sum_bases + 1)
    hitter.HR += 1
    pitcher.HR += 1
    hitter.H += 1
    hitter.TB += 4
    return runs_scored, base_state

# assigning results with coresponding functions we made above
outcome_funcs = {
    'HR':homerun,
    '3B':triple,
    '2B':double,
    '1B':single,
    'BB':bb,
    'HBP':hbp,
    'IPO':IPO,
    'SO':K,
}


# come back to bullpen thing later
def half_inning(hitting_team_lineup, pitcher, pitching_team_bullpen, current_batsmen_index, game_num, inning_num):
    outs = 0
    base_state = [None, None, None]
    index = current_batsmen_index

    if index >= len(hitting_team_lineup):
        index = 0

    current_pitcher = pitcher
    runs_scored_in_half_inning = 0

    sequence = []
    # incrementing outs wrong i think for now keep at 4 and it should work.......fix later!!!
    while outs < 3:
        pa_result, outs_on_play = PA(hitting_team_lineup[index], current_pitcher, game_num, inning_num)
        # move bases based on result
        # determine which function to call
        func = [func for result, func in outcome_funcs.items() if result == pa_result][0]
        # call it
        runs_scored, base_state = func(hitting_team_lineup[index], pitcher, base_state)
        hitting_team_lineup[index].RBI += runs_scored
        hitting_team_lineup[index].team.runs += runs_scored
        pitcher.ER += runs_scored
        # increment stuff and check position in lineup
        runs_scored_in_half_inning += runs_scored
        sequence.append(pa_result)
        outs += outs_on_play
        index += 1
        if index >= len(hitting_team_lineup):
            index = 0
    pitcher.IP += 1
    return runs_scored_in_half_inning, index, sequence


def full_inning(home_team, away_team, home_pitcher, away_pitcher, current_home_batsmen_index, current_away_batsmen_index, game_num, inning_num):

    next_in_lineup_home = [current_home_batsmen_index]
    next_in_lineup_away = [current_away_batsmen_index]
    sequence_of_events = []

    away_score = 0
    home_score = 0

    next_in_line_away = next_in_lineup_away[-1]
    runs_scored_away, next_away_batter_index, result_sequence = half_inning(away_team.lineup, home_pitcher, away_team.bullpen, next_in_line_away, game_num, inning_num)
    next_in_lineup_away.append(next_away_batter_index)
    away_score += runs_scored_away
    sequence_of_events.append(result_sequence)
                    
    next_in_line_home = next_in_lineup_home[-1]
    runs_scored_home, next_home_batter_index, result_sequence = half_inning(home_team.lineup, away_pitcher, home_team.bullpen, next_in_line_home, game_num, inning_num)
    next_in_lineup_home.append(next_home_batter_index)
    sequence_of_events.append(result_sequence)
    home_score += runs_scored_home

    return home_score, away_score, next_home_batter_index, next_away_batter_index, sequence_of_events



def game(home_team, away_team, home_pitcher, away_pitcher, start_inning, game_num, current_batsmen_index_home = 0, current_batsmen_index_away = 0, home_start_score = 0, away_start_score = 0):

        # for now forcing start inning to be 0 for testing and likley beta version
        start_inning = 1


        home_score = home_start_score
        away_score = away_start_score
        next_in_lineup_home = [current_batsmen_index_home]
        next_in_lineup_away = [current_batsmen_index_away]
        sequence_of_events = []
        innings = start_inning
        
        # meaning if the user input to begin simulation in the top of an inning like normal person
        for i in range(9): # want to figure out how to cycle through relievers after a certain inning
                next_home_batter_index = next_in_lineup_home[-1]
                next_away_batter_index = next_in_lineup_away[-1]
                runs_scored_home, runs_scored_away, next_home_batter_index, next_away_batter_index, result_sequence = full_inning(home_team, away_team, home_pitcher, away_pitcher, current_batsmen_index_home, current_batsmen_index_away, game_num, innings)
                sequence_of_events.append(result_sequence)
                next_in_lineup_home.append(next_home_batter_index)
                next_in_lineup_away.append(next_away_batter_index)
                home_score += runs_scored_home
                away_score += runs_scored_away
                innings += 1
            # extra innings
        while home_score == away_score:
                next_home_batter_index = next_in_lineup_home[-1]
                next_away_batter_index = next_in_lineup_away[-1]
                runs_scored_home, runs_scored_away, next_home_batter_index, next_away_batter_index, result_sequence = full_inning(home_team, away_team, home_pitcher, away_pitcher, current_batsmen_index_home, current_batsmen_index_away, game_num, innings)
                sequence_of_events.append(result_sequence)
                next_in_lineup_home.append(next_home_batter_index)
                next_in_lineup_away.append(next_away_batter_index)
                home_score += runs_scored_home
                away_score += runs_scored_away
                innings += 1

        # increment wins and losses
        if home_score > away_score:
            home_team.wins += 1
            away_team.losses += 1
            if innings > 9:
                home_team.extra_inning_wins += 1
            return home_team, next_home_batter_index, next_away_batter_index
        elif away_score > home_score:
            away_team.wins += 1
            home_team.losses += 1
            if innings > 9:
                away_team.extra_inning_wins += 1
            return away_team, next_home_batter_index, next_away_batter_index

def simulation(num_simulations, home_team, away_team, start_inning = 1, beginnnig_batsmen_index_home = 0, beginning_batsmen_index_away = 0, home_team_start_score = 0, away_team_start_score = 0):
    games_played = 1
    # ask user about splitting home/away 50/50 or to do one team as home the whole time at some point as well as manual lineups    
    # goals: keep track of records live with st.metrics, make a graph, and downloadable csv file w/ pbp data
    data = []
    home_pitching_index = 0
    away_pitching_index = 0

    home_batting_next_up = [0]
    away_batting_next_up= [0]

    with st.spinner(f"\nSimulating {num_simulations} baseball games..."):
        for i in range(num_simulations // 2):
            
            previous_result, home_index_next, away_index_next = game(home_team, away_team, home_team.rotation[home_pitching_index], away_team.rotation[away_pitching_index], start_inning = start_inning, game_num = games_played, current_batsmen_index_away=away_batting_next_up[-1], current_batsmen_index_home=home_batting_next_up[-1])
            home_pitching_index += 1
            away_pitching_index += 1


            if home_pitching_index >= len(home_team.rotation):
                home_pitching_index = 0

            if away_pitching_index >= len(away_team.rotation):
                away_pitching_index = 0
            
            if away_index_next >= len(away_team.lineup):
                away_index_next = 0
            
            if home_index_next >= len(home_team.lineup):
                home_index_next = 0

            away_batting_next_up.append(away_index_next)
            home_batting_next_up.append(home_index_next)

            games_played += 1

            data.append([home_team.wins, away_team.wins, games_played])


        # branching this so we can figure out deltas
        for i in range(num_simulations // 2):
                previous_result, home_index_next, away_index_next = game(away_team, home_team, away_team.rotation[away_pitching_index], home_team.rotation[home_pitching_index], start_inning = start_inning, current_batsmen_index_away=away_batting_next_up[-1], current_batsmen_index_home=home_batting_next_up[-1], game_num = games_played)
                home_pitching_index += 1
                away_pitching_index += 1

                if home_pitching_index >= len(home_team.rotation):
                    home_pitching_index = 0

                if away_pitching_index >= len(away_team.rotation):
                    away_pitching_index = 0

                if away_index_next >= len(away_team.lineup):
                    away_index_next = 0

                if home_index_next >= len(home_team.lineup):
                    home_index_next = 0

                away_batting_next_up.append(away_index_next)
                home_batting_next_up.append(home_index_next)

                games_played += 1

                data.append([home_team.wins, away_team.wins, games_played])

    df = pd.DataFrame(data, columns = [f"{home_team.name.split()[-1]} Wins", f"{away_team.name.split()[-1]} Wins", "Game#"])
    df.set_index("Game#", inplace = True)
    pbp_df = pd.DataFrame(pbp_data, columns = pbp_cols)

    # make sure it is this simulation only
    

    # pbp_csv = convert_df(pbp_df)
    # st.download_button("Download Play By Play Data", data = pbp_csv, file_name = "Ball.Sim_pbp.csv")


    return pbp_df, df