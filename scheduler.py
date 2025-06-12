import time
from itertools import combinations
import math

class TournamentScheduler:
    def __init__(self, players, max_duration_seconds=10):
        self.players = players
        self.max_duration_seconds = max_duration_seconds
        n = len(players)
        self.max_pairs = (n // 4) * 2
        self.min_rounds = (n - 1) + (n % 4)

    def generate_schedule(self):
        start = time.time()
        names = [p.name for p in self.players]
        all_pairs = {(a, b) if a < b else (b, a) for a, b in combinations(names, 2)}

        temp = list(names)
        dummy = None
        if len(temp) % 2 == 1:
            dummy = '__BYE__'
            temp.append(dummy)
        num_rr = len(temp) - 1
        half = len(temp) // 2

        rounds = []
        used_pairs = set()

        # Circle method
        for _ in range(num_rr):
            if time.time() - start > self.max_duration_seconds:
                break
            round_candidates, byes = [], []
            for i in range(half):
                a, b = temp[i], temp[-i-1]
                if a == dummy and b == dummy: continue
                if a == dummy: byes.append(self._get_player(b)); continue
                if b == dummy: byes.append(self._get_player(a)); continue
                pair = (a,b) if a< b else (b,a)
                if pair not in used_pairs: round_candidates.append(pair)
            temp = [temp[0]] + [temp[-1]] + temp[1:-1]

            selected, used_in_round = [], set()
            for pair in round_candidates:
                if len(selected)>=self.max_pairs: break
                a,b = pair
                if a not in used_in_round and b not in used_in_round:
                    selected.append(pair)
                    used_in_round.update([a,b])
            pairs = [(self._get_player(a), self._get_player(b)) for a,b in selected]
            used_pairs.update(selected)

            extras = [p for p in round_candidates if p not in selected]
            for a,b in extras:
                byes.extend([self._get_player(a), self._get_player(b)])
            for p in set(byes): p.byes+=1
            rounds.append((pairs,byes))

        # Remaining
        remaining = list(all_pairs - used_pairs)
        while remaining or len(rounds)<self.min_rounds:
            if time.time() - start > self.max_duration_seconds: break
            sel, used_in_round = [], set()
            for pair in remaining:
                if len(sel)>=self.max_pairs: break
                a,b = pair
                if a not in used_in_round and b not in used_in_round:
                    sel.append(pair); used_in_round.update([a,b])
            remaining = [p for p in remaining if p not in sel]
            pairs = [(self._get_player(a), self._get_player(b)) for a,b in sel]
            byes = [p for p in self.players if p.name not in used_in_round]
            for p in byes: p.byes+=1
            used_pairs.update(sel)
            rounds.append((pairs,byes))
            if not remaining and len(rounds)>=self.min_rounds: break

        if len(rounds)>self.min_rounds:
            rounds=rounds[:self.min_rounds]
        return rounds

    def _get_player(self,name):
        for p in self.players:
            if p.name==name: return p
        raise ValueError


def generate_schedule(players, max_duration_seconds=10):
    return TournamentScheduler(players,max_duration_seconds).generate_schedule()