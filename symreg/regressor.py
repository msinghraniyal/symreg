from time import time

from symreg.ga import GA
from symreg.nsgaii import ndim_pareto_ranking, SolutionScore


class Regressor:
    def __init__(
            self,
            n=50,
            duration=float('inf'),
            generations=float('inf'),
            stagnation_limit=float('inf'),
            verbose=False,
            zero_program_chance=0.5,
            grow_root_mutation_chance=.3,
            grow_leaf_mutation_chance=.4,
            int_std=3,
            float_std=4,
    ):
        self._ga = GA(
            n=n,
            zero_program_chance=zero_program_chance,
            grow_root_mutation_chance=grow_root_mutation_chance,
            grow_leaf_mutation_chance=grow_leaf_mutation_chance,
            int_std=int_std,
            float_std=float_std,
        )
        self.duration = duration
        self.verbose = verbose
        self.columns = ()
        self.training_details = {'steps': 0, 'duration': 0}
        self.steps_to_take = generations
        self.max_stagnation_generations = stagnation_limit
        self._last_results = {}
        self._stagnation = 0

    def fit(self, X, y):
        start = time()
        self._ga.fit(X, y)
        last_printed = time()
        taken = time() - start

        while self.can_continue(taken):
            taken = time() - start
            if self.verbose and time() - last_printed > 10:
                last_printed = time()
                print(f'Time left  : {int(self.duration - taken + .9)}s')
                print(f'Best so far: {min(s for s in self._ga.old_scores.values())} (error, complexity)')

            self._ga.fit_partial(X, y)

            new_results = self.results()
            if new_results != self._last_results:
                self._stagnation = 0
                self._last_results = new_results
            else:
                self._stagnation += 1

            self.training_details = {
                'generations': self._ga.steps_taken,
                'stagnated_generations': self._stagnation,
                'duration': time() - start,
            }

        if self.verbose:
            print(f'Complete. {self.training_details}')

    def can_continue(self, taken):
        return taken < self.duration and \
               self._ga.steps_taken < self.steps_to_take and \
               self._stagnation < self.max_stagnation_generations

    def predict(self, X):
        y_pred = self._ga.predict(X)
        return y_pred

    def results(self):
        scores = self._ga.old_scores
        scores = SolutionScore.scores_from_dict(scores)
        front = ndim_pareto_ranking(scores)[1]
        front = [{'error': ss.scores[0], 'complexity': ss.scores[1], 'program': ss.individual} for ss in front]
        return sorted(front, key=lambda s: s['complexity'])

