import streamlit as st
import warnings
warnings.simplefilter(action='ignore')


class Hitter():

    def __init__(self, name, df, team):

        self.name = name
        self.df = df
        self.weird = False
        self.throws = self.df.at[0, 'Throws']
        self.bats = self.df.at[0, 'Bats']
        self.team = team

        # meaning if they only have splits versus one type of pitcher somehow
        if len(self.df[self.df['Split'] == 'vs LHP'].index) < 1:
            self.weird = True
        elif len(self.df[self.df['Split'] == 'vs RHP'].index) < 1:
            self.weird = True

        if self.weird == False:
            self.probsr, self.probsl = self.probabilities()

        # keep track of statistics
        self.PA = 0
        self.AB = 0
        self.H = 0
        self.singles = 0
        self.doubles = 0
        self.triples = 0
        self.HR = 0
        self.BB = 0
        self.HBP = 0
        self.ROE = 0
        self.K = 0
        self.IPO = 0
        self.TB = self.singles + (self.doubles * 2) + (self.triples * 3) + (self.HR * 4)
        self.RBI = 0

    def probabilities(self):

        self.df['1B'] = self.df['H'] - (self.df['2B'] + self.df['3B'] + self.df['HR'])
        self.df['ATT'] = self.df['SB'] + self.df['CS']
        self.df['IPO'] = self.df['PA'] - (self.df['H'] + self.df['BB'] + self.df['HBP']) # make sure this is correct.

        vrhp = self.df[self.df['Split'] == 'vs RHP']
        vlhp = self.df[self.df['Split'] == 'vs LHP']
        vrhp.reset_index(drop = True, inplace = True)
        vlhp.reset_index(drop = True, inplace = True)

        probsr = []
        probsl = []

        for col in vrhp.columns:
            if type(vrhp.at[0, col]) != str:
                probsr.append([col, vrhp.at[0, col] / vrhp.at[0, 'PA']])

        for col in vlhp.columns:
            if type(vlhp.at[0, col]) != str:
                probsl.append([col, vlhp.at[0, col] / vlhp.at[0, 'PA']])

        return probsr, probsl

    def display_rate_stats(self):
        slg = self.TB / self.AB
        obp = (self.H + self.BB + self.HBP + self.ROE) / self.AB
        avg = self.H / self.AB
        st.write(f"{self.name}|PA {self.PA}|AVG {avg:.3f}|OBP {obp:.3f}|SLG {slg:.3f}|HR {self.HR}|RBI {self.RBI}|")



class Pitcher():

    def __init__(self, name, df, team):

        self.name = name
        self.df = df
        self.weird = False
        self.bats = self.df.at[0, 'Bats']
        self.throws = self.df.at[0, 'Throws']
        self.team = team

        # meaning if they only have splits against one kind of hitter somehow
        if len(self.df[self.df['Split'] == 'vs LHB'].index) < 1:
            self.weird = True
        elif len(self.df[self.df['Split'] == 'vs RHB'].index) < 1:
            self.weird = True

        if self.weird == False:
            self.probsr, self.probsl = self.probabilities()
        
        # keep track of statistics
        self.BF =  0
        self.IP = 0
        self.K = 0
        self.H = 0
        self.BB = 0
        self.HBP = 0
        self.ER = 0
        self.R = 0
        self.IPO = 0
        self.doubles = 0
        self.singles = 0
        self.triples = 0
        self.HR = 0
    
    def probabilities(self):

        self.df['1B'] = self.df['H'] - (self.df['2B'] + self.df['3B'] + self.df['HR'])
        self.df['ATT'] = self.df['SB'] + self.df['CS']
        self.df['IPO'] = self.df['PA'] - (self.df['H'] + self.df['BB'] + self.df['HBP']) # make sure this is correct.

        vrhh = self.df[self.df['Split'] == 'vs RHB']
        vlhh = self.df[self.df['Split'] == 'vs LHB']
        vrhh.reset_index(drop = True, inplace = True)
        vlhh.reset_index(drop = True, inplace = True)

        probsr = []
        probsl = []        

        for col in vrhh.columns:
            if type(vrhh.at[0, col]) != str:
                probsr.append([col, vrhh.at[0, col] / vrhh.at[0, 'PA']])

        for col in vlhh.columns:
            if type(vlhh.at[0, col]) != str:
                probsl.append([col, vlhh.at[0, col] / vlhh.at[0, 'PA']])

        return probsr, probsl

    def display_rate_stats(self):
        era = (9 * self.ER) / self.IP
        whip = (self.BB + self.H) / self.IP
        k_9 = self.K / (self.IP / 9)
        bb_9 = self.BB / (self.IP / 9)
        avg_agnst = self.H / (self.BF - self.HBP)

        st.write(f"{self.name}|IP {self.IP}|ERA {era:.2f}|WHIP {whip:.2f}|K/9 {k_9:.2f}|BB/9 {bb_9:.2f}|")        

# cache teams??
class Team():

    def __init__(self, team_name, year, data_list, lineup_settings):

        self.name = team_name
        self.year = year
        self.data = data_list

        # right now the lineup settings are auto until we launch the manual lineup function
        self.lineup_settings = lineup_settings

        self.hitters, self.pitchers = self.generate_players(self.data)

        if lineup_settings == 'auto':
            self.lineup, self.rotation, self.bullpen = self.set_lineups_auto()

        self.wins = 0
        self.losses = 0
        self.extra_inning_wins = 0
        self.runs = 0

    def generate_players(self, df):

        # get list of all unique names in the df
        names = df['Name'].unique()

        hitters = []
        pitchers = []
        # then for each player we should single their section of the df out
        for name in names:
            player_df = df[df['Name'] == name]
            player_df.reset_index(drop = True, inplace = True)

            # then determine if they are a hitter or pitcher based on the split column
            if player_df.at[0, 'Split'] == 'vs RHB':
                pitchers.append(Pitcher(name, player_df, self))
            elif player_df.at[0, 'Split'] == 'vs RHP':
                hitters.append(Hitter(name, player_df, self))
            
        return hitters, pitchers

    def set_lineups_auto(self):
        # the pitchers and hitters seem to have the same columns, weird.
        rotation = sorted(self.pitchers, key=lambda x: sum(x.df['PA']), reverse = True)[:6]
        bullpen = [pitcher for pitcher in self.pitchers if pitcher not in rotation] # everyone else goes in the pen
        lineup = sorted(self.hitters, key=lambda x: sum(x.df['PA']), reverse = True)[:9]
        return lineup, rotation, bullpen
