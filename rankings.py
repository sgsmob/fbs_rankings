import sys
import csv
import datetime
import random
import os
import networkx as nx
from sklearn.naive_bayes import GaussianNB

       
class Team:
    def __init__(self, name, win_score, loss_score):
        self.name = name
        self.win_score = win_score
        self.loss_score = loss_score
        
    def combined_scores(self):
        return 2*self.win_score - 7*self.loss_score


class Game:
    def __init__(self, winner, loser, date, week, name):
        self.winner = winner
        self.loser = loser
        self.date = date
        self.week = week
        self.name = name
        
    def is_bowl(self):
        return (self.date.month == 1 or (self.date.month == 12 and self.date.day > 14))
        
    def __str__(self):
        return self.name


def canonical_name(name):
    if name[0] == "(":
        for i, c in enumerate(name):
            if c == ")":
                return name[i+2:]
    else:
        return name


def date_from_string(date_string):
    month_map = {"Jan": 1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}
    month, day, year = date_string.split()
    return datetime.date(int(year), month_map[month], int(day))


def prune(G):
    removal = []
    for v in G.nodes():
        if G.in_degree(v) + G.out_degree(v) < 10:
            removal.append(v)
            # raise ValueError("{} should have won more than {} or lost more than {} games".format(v, G.in_degree(v), G.out_degree(v)))
    G.remove_nodes_from(removal)

# Results from https://www.sports-reference.com/cfb/.
def load_results_from_file(filename):
    with open(filename, 'r') as input:
        csvreader = csv.DictReader(input, delimiter=',')
        G = nx.DiGraph()
        bowls = []
        for row in csvreader:
            winner = canonical_name(row["Winner"])
            loser = canonical_name(row["Loser"])
            date = date_from_string(row["Date"])
            week = int(row["Wk"])
            name = row["Notes"]
            game = Game(winner, loser, date, week, name)
            if game.is_bowl():
                bowls.append(game)
            else:
                G.add_edge(game.loser, game.winner)
    # sanity_check(G)
    prune(G)
    return G, bowls
 
 
def scored_teams(G):
    win_scores = nx.pagerank_numpy(G, alpha=0.9)
    loss_scores = nx.pagerank_numpy(G.reverse(), alpha=0.9)
    return {team: Team(team, win_score, loss_scores[team]) for team, win_score in win_scores.items()}
    

def decide(bowls, teams, model):
    for bowl in bowls:
        #score = teams[bowl.winner].combined_scores() - teams[bowl.loser].combined_scores()
        w_team = teams[bowl.winner]
        l_team = teams[bowl.loser]
        score = model.predict_prob([w_team.win_score, w_team.loss_score, l_team.win_score, l_team.loss_score])
        if score[1] > score[0]:
            yield score[1], bowl.name, bowl.winner
        else:
            yield score[0], bowl.name, bowl.loser


def train(teams_by_year, bowls_by_year):
    training_data = []
    training_labels = []
    for year in sorted(bowls_by_year.keys())[:-1]:
        current_bowls = bowls_by_year[year]
        current_teams = teams_by_year[year]
        for bowl in current_bowls:
            wws = current_teams[bowl.winner].win_score
            wls = current_teams[bowl.winner].loss_score
            lws = current_teams[bowl.loser].win_score
            lls = current_teams[bowl.loser].loss_score
            if random.randint(0, 1) == 1:
                training_data.append([wws, wls, lws, lls])
                training_labels.append(1)
            else:
                training_data.append([lws, lls, wws, wls])
                training_labels.append(0)
    model = GaussianNB()
    return model.fit(training_data, training_labels)
    

if __name__ == "__main__":
    results_dir, out_file = sys.argv[1:]
    years = sorted(os.listdir(results_dir))
    CURRENT_YEAR = years[-1]
    bowls_by_year = {}
    teams_by_year = {}
    for year in years:
        results_file = os.path.join(results_dir, year, "results.csv")
        G, bowls = load_results_from_file(results_file)
        teams = scored_teams(G)
        bowls_by_year[year] = bowls
        teams_by_year[year] = teams
    model = train(teams_by_year, bowls_by_year)
    for x in sorted(teams_by_year[CURRENT_YEAR].values(), key=lambda x: x.combined_scores()):
        print(x.name, x.combined_scores())
    with open(out_file, 'w') as out:
        for result in sorted(decide(bowls_by_year[CURRENT_YEAR], teams_by_year[CURRENT_YEAR], model)):
            out.write("{},{},{}\n".format(*result))

