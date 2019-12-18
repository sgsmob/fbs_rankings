import networkx as nx
import sys
import csv
import datetime

class Bowl:
    def __init__(self, name, away, home):
        self.name = name
        self.away = away
        self.home = home
        
    def score_diff(self):
        return self.away.combined_scores() - self.home.combined_scores()
        
    def __str__(self):
        return self.name

        
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


def sanity_check(G):
    for v in G.nodes():
        if G.in_degree(v) + G.out_degree(v) < 10:
            raise ValueError("{} should have won more than {} or lost more than {} games".format(v, G.in_degree(v), G.out_degree(v)))


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
    return G, bowls
 
 
def scored_teams(G):
    win_scores = nx.pagerank_numpy(G, alpha=0.9)
    loss_scores = nx.pagerank_numpy(G.reverse(), alpha=0.9)
    return {team: Team(team, win_score, loss_scores[team]) for team, win_score in win_scores.iteritems()}
    

def decide(bowls, teams):
    for bowl in bowls:
        score = teams[bowl.winner].combined_scores() - teams[bowl.loser].combined_scores()
        if score > 0:
            yield score, bowl.name, bowl.winner
        else:
            yield -1*score, bowl.name, bowl.loser
            

if __name__ == "__main__":
    results_file, out_file = sys.argv[1:]
    G, bowls = load_results_from_file(results_file)
    teams = scored_teams(G)
    for x in sorted(teams.values(), key=lambda x: x.combined_scores()):
        print x.name, x.combined_scores()
    with open(out_file, 'w') as out:
        for result in sorted(decide(bowls, teams)):
            out.write("{},{},{}\n".format(*result))
        
    
    