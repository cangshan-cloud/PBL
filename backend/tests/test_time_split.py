import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.research import Observation
from app.domain.time_split import evaluate_time_split


class TimeSplitTests(unittest.TestCase):
    def test_embargoes_last_research_signal_and_keeps_periods_disjoint(self):
        start = date(2025, 1, 1)
        observations = [Observation(start + timedelta(days=day), symbol, factor, .01 * (day + index))
                        for day in range(6) for index, (symbol, factor) in enumerate((('A', 1), ('B', 2)))]
        result = evaluate_time_split(observations, '2025-01-05', groups=2,
                                     winsorize=False, standardize=False, mad_scale=3)
        self.assertEqual(result['embargo_signal_date'], '2025-01-04')
        self.assertEqual(result['research']['end_date'], '2025-01-03')
        self.assertEqual(result['validation']['start_date'], '2025-01-05')
        self.assertEqual(result['research']['observation_count'], 6)
        self.assertEqual(result['validation']['observation_count'], 4)
        self.assertEqual(result['research']['valid_ic_dates'], 3)

    def test_rejects_too_short_periods(self):
        observations = [Observation(date(2025, 1, day), 'A', float(day), .01) for day in range(1, 5)]
        with self.assertRaisesRegex(ValueError, 'at least 3 research and 2 validation'):
            evaluate_time_split(observations, '2025-01-03', groups=2,
                                winsorize=True, standardize=True, mad_scale=3)
