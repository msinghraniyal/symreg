from collections import defaultdict
import math


def _fillna(series, fill_value):
    def _replace_elem(x):
        return fill_value if math.isnan(x) else x
    return tuple(_replace_elem(i) for i in series)


class SolutionScore:
    """And individual together with its score, used for fast nondominated sort"""

    def __init__(self, individual, scores):
        self.individual = individual
        self.scores = scores

    @classmethod
    def scores_from_dict(cls, score_dict: dict):
        return {cls(p, p_scores) for p, p_scores in score_dict.items()}

    def dominates(self, other):
        """Smaller error is better"""
        my_scores = _fillna(self.scores, float('inf'))
        other_scores = _fillna(other.scores, float('inf'))

        at_least_as_good = all(s <= o for s, o in zip(my_scores, other_scores))
        better_in_some_respect = any(s < o for s, o in zip(my_scores, other_scores))

        return at_least_as_good and better_in_some_respect

    def __repr__(self):
        return f'SolutionScore({self.individual}, {self.scores})'

    def __eq__(self, other):
        """Needed otherwise duplication occurs in sets/dicts"""
        return self.individual == other.individual and self.scores == other.scores

    def __hash__(self):
        return hash(self.individual) + hash(self.scores)


def fast_non_dominated_sort(scores: dict) -> dict:
    """
        Group individuals by rank of their Pareto
        Tries to stay close to the paper's implementation (albeit it is quite long and imperative)
        :param scores: {individual -> (score1, score2, ...)}
        :returns {individual: Pareto rank}
    """

    S = defaultdict(set)  # p is superior to individuals in S[p]
    n = defaultdict(lambda: 0)      # p is dominated by n[p] individuals
    fronts = defaultdict(set)  # individuals in front 1 are fronts[1]

    # Create domination map
    for p in SolutionScore.scores_from_dict(scores):
        for q in SolutionScore.scores_from_dict(scores):
            if p.dominates(q):
                S[p].update({q})
            elif q.dominates(p):
                n[p] += 1

        if n[p] == 0:
            fronts[1].update({p})

    # Iteratively eliminate current Pareto frontier, and find members of next best
    i = 1
    while fronts[i]:
        Q = set()   # Next front

        for p in fronts[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    Q.update({q})
        i += 1
        fronts[i] = Q

    return {key: {v.individual for v in value} for key, value in fronts.items() if value}


def _peek_any(set_or_dict):
    return list(set_or_dict)[0]


def crowding_distance_assignment(scores: dict) -> dict:
    """
        Calculate crowding
        Implemented as dimension-normalized distance between the 2 surrounding neighbors from given Pareto front
        Tries to stay close to the paper's implementation (albeit it is quite long and imperative)
        :param scores: {individual -> (score1, score2, ...)}
        :returns {individual: distance}
    """

    distance = {i: 0 for i in scores}

    try:
        M = len(_peek_any(scores.values())) # number of objectives
        for m in range(M):
            I = sorted(scores.keys(), key=lambda i: scores[i][m])   # Sort using each objective value
            I = tuple(I)

            distance[I[0]] = distance[I[-1]] = float('inf')         # boundary points are always selected
            fm_min, fm_max = scores[I[0]][m], scores[I[-1]][m]
            for i in range(1, len(I)-1):
                earlier = scores[I[i + 1]]
                later = scores[I[i - 1]]
                space = (earlier[m] - later[m])
                normalized = (fm_max - fm_min)
                distance[I[i]] += space / normalized

    except IndexError:
        # _peek_any failed: we don't have any individuals
        pass

    return distance


def nsgaii_cull(start_pop, n_out):
    """
    Remove individuals that are not fit enough according to NSGA-II

    :param start_pop:   {individual -> (score1, score2, ...), ...}
    :param n_out:       number of individuals to survive
    :return:            {individual -> (score1, score2, ...), ...}
    """
    pareto_front = fast_non_dominated_sort(start_pop)
    crowding_distance = crowding_distance_assignment(start_pop)
    end_pop = []
    for front in sorted(pareto_front.keys()):
        sorted_front = sorted(pareto_front[front], key=lambda i: -crowding_distance[i])
        end_pop.extend(sorted_front)

        if len(end_pop) > n_out:
            break

    return {i: start_pop[i] for i in end_pop[:n_out]}


if __name__ == '__main__':
    import pytest

    pytest.main(['test_nsgaii.py', '-vv'])