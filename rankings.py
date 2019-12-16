import networkx as nx
import sys

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


def sanity_check(G):
    for v in G.nodes():
        if G.in_degree(v) + G.out_degree(v) < 10:
            raise ValueError("{} should have won more than {} or lost more than {} games".format(v, G.in_degree(v), G.out_degree(v)))
        
    
def load_results_from_file(filename):
    with open(filename, 'r') as input:
        G = nx.DiGraph()
        for line in input:
            tokens = line.strip().split()
            winner = tokens[0]
            for loser in tokens[1:]:
                G.add_edge(loser, winner)
    sanity_check(G)
    return G
 
 
def load_bowls_from_file(filename, teams):
    with open(filename, 'r') as input:
        for line in input:
            name, away, home = line.strip().split()
            yield Bowl(name, teams[away], teams[home])
 
 
def scored_teams(G):
    win_scores = nx.pagerank_numpy(G, alpha=0.9)
    loss_scores = nx.pagerank_numpy(G.reverse(), alpha=0.9)
    return {team: Team(team, win_score, loss_scores[team]) for team, win_score in win_scores.iteritems()}
    

def decide(bowls):
    for bowl in bowls:
        score = bowl.score_diff()
        if score > 0:
            yield score, bowl.name, bowl.away.name
        else:
            yield -1*score, bowl.name, bowl.home.name
            

if __name__ == "__main__":
    results_file, bowls_file, out_file = sys.argv[1:]
    teams = scored_teams(load_results_from_file(results_file))
    for x in sorted(teams.values(), key=lambda x: x.combined_scores()):
        print x.name, x.combined_scores()
    with open(out_file, 'w') as out:
        for result in sorted(decide(load_bowls_from_file(bowls_file, teams))):
            out.write("{},{},{}\n".format(*result))
        
    
    