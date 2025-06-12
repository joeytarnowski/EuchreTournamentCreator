from player import Player
from scheduler import generate_schedule

class Tournament:
    def __init__(self, player_names):
        self.players = [Player(n) for n in player_names]
        self.rounds=[]
        self.current_round=0
        self.scores=[]

    def generate_full_schedule(self,_=None):
        self.rounds = generate_schedule(self.players)
        # ensure NSP filling
        n=len(self.players)
        max_pairs=(n//4)*2
        for i,(pairs,byes) in enumerate(self.rounds):
            while len(pairs)<max_pairs and byes:
                p=byes.pop(0)
                pairs.append((p,None))
            self.rounds[i]=(pairs,byes)
        self.scores=[[0]*len(pairs) for pairs,_ in self.rounds]

    def next_round(self):
        if self.current_round>=len(self.rounds): return [],[]
        pairs,byes=self.rounds[self.current_round]
        self.current_round+=1
        return pairs,byes

    def record_result(self,game,pair,points):
        r=self.current_round-1
        idx=self.rounds[r][0].index(pair)
        self.scores[r][idx]=points
        for p in pair:
            if p: p.add_score(game, points)

    def get_leaderboard(self):
        return sorted(self.players,key=lambda p:p.score,reverse=True)

    def get_round_history(self): return self.rounds,self.scores