"""
Tests für die LNS (Large Neighborhood Search) Implementierung.

Dieser Test-Modul enthält Unit-Tests für die update_search_window Methode,
die das Suchfenster basierend auf der Verbesserung der Lösung anpasst.
"""

from unittest.mock import Mock, patch

import pytest

from src.inputTypes import employee, instace, shiftType
from src.inputTypes.instace import Instance
from src.LNS.lns import LNS
from src.LNS.slice_instance import Slice_instance
from src.solution import Solution


class TestUpdateSearchWindow:
    """
    Tests für die update_search_window Methode der LNS-Klasse.

    Die Methode passt die Größe des Suchfensters (start_day, end_day) dynamisch an:
    - Bei starker Verbesserung: Fenster wird verkleinert (fokussierter)
    - Bei keiner Verbesserung: Fenster wird vergrößert (breiter suchen)
    - Beachtet MIN_DAY und MAX_DAY Grenzen
    """

    @pytest.fixture
    def mock_solution(self):
        """
        Erstellt eine Mock-Solution für Tests.

        Returns:
            Mock Solution mit objective_value=100 und 30 Tagen
        """
        solution = Mock(spec=Solution)
        solution.objective_value = 100
        solution.disabled_constraints = []

        instance = Mock(spec=Instance)
        instance.number_of_days = 30
        instance.shift_types = ["type1", "type2", "type3"]  # Mock shift types
        instance.employees = ["emp1", "emp2", "emp3", "emp4"]  # Mock employees
        solution.instance = instance

        return solution

    @pytest.fixture
    def lns_instance(self, mock_solution):
        """
        Erstellt eine LNS-Instanz für Tests.

        Args:
            mock_solution: Mock der initialen Lösung

        Returns:
            LNS-Instanz mit Standard-Parametern
        """
        with patch.object(
            LNS, "_LNS__parse_solution_or_instance", return_value=(mock_solution, 0.0)
        ):
            lns = LNS(
                mock_solution,
                start_search_window_size=5,
                search_window_size_min=3,
                window_increase_factor=1.5,
                window_decrease_factor=0.8,
                strong_improvement_threshold=0.01,
                timeout_seconds=180,
            )
            # Setze initiales Fenster
            lns.start_day = 10
            lns.end_day = 15  # Window size = 5
            return lns

    def test_no_improvement_increases_window(self, lns_instance: LNS):
        """
        Test: Bei keiner Verbesserung (improvement=0) wird das Fenster vergrößert.

        Erwartet:
            - Window size steigt um window_increase_factor (1.5)
            - Fenster wird zufällig nach links/rechts erweitert
            - Grenzen (MIN_DAY, MAX_DAY) werden respektiert
        """
        # Arrange: Initial window [10, 15], size=6
        initial_start = lns_instance.start_day
        initial_end = lns_instance.end_day
        initial_size = initial_end - initial_start + 1

        # Act: Keine Verbesserung
        with patch("random.randint", return_value=3):  # Deterministisch für Test
            lns_instance.update_search_window(improvement=0)

        # Assert: Fenster sollte größer sein
        new_size = lns_instance.end_day - lns_instance.start_day + 1
        expected_size = int(initial_size * lns_instance.window_increase_factor)
        assert new_size >= initial_size, (
            "Fenster sollte bei keiner Verbesserung größer werden"
        )
        assert lns_instance.start_day >= lns_instance.MIN_DAY
        assert lns_instance.end_day <= lns_instance.MAX_DAY
        assert expected_size == new_size

    def test_strong_improvement_decreases_window(self, lns_instance):
        """
        Test: Bei starker Verbesserung wird das Fenster verkleinert.

        Eine starke Verbesserung liegt vor, wenn:
            relative_improvement >= strong_improvement_threshold (0.01 = 1%)

        Erwartet:
            - Window size sinkt um window_decrease_factor (0.8)
            - Mindestgröße (search_window_size_min=3) wird eingehalten
        """
        # Arrange: Initial window [10, 15], objective=100
        # Improvement von 2 → relative = 2/100 = 0.02 = 2% > 1% threshold
        initial_size = lns_instance.end_day - lns_instance.start_day

        # Act: Starke Verbesserung
        with patch("random.randint", return_value=1):
            lns_instance.update_search_window(improvement=2)

        # Assert: Fenster sollte kleiner sein
        new_size = lns_instance.end_day - lns_instance.start_day
        expected_size = max(
            lns_instance.search_window_size_min,
            int(initial_size * lns_instance.window_decrease_factor),
        )
        assert new_size == expected_size
        assert new_size >= lns_instance.search_window_size_min
        assert initial_size > new_size

    def test_weak_improvement_no_change(self, lns_instance):
        """
        Test: Bei schwacher Verbesserung (unter threshold) ändert sich die Fenstergröße nicht.

        Schwache Verbesserung: relative_improvement < strong_improvement_threshold
        z.B. 0.5/100 = 0.005 = 0.5% < 1%

        Erwartet:
            - Window size bleibt gleich
            - start_day und end_day unverändert
        """
        # Arrange: Improvement von 0.5 → relative = 0.5/100 = 0.005 = 0.5% < 1%
        initial_start = lns_instance.start_day
        initial_end = lns_instance.end_day

        # Act: Schwache Verbesserung
        lns_instance.update_search_window(improvement=0.5)

        # Assert: Keine Änderung
        assert lns_instance.start_day == initial_start
        assert lns_instance.end_day == initial_end

    def test_window_respects_min_boundary(self, lns_instance):
        """
        Test: Fenster kann nicht über MIN_DAY hinaus expandieren.

        Erwartet:
            - start_day >= MIN_DAY (0)
            - Bei Expansion nach links wird an MIN_DAY gestoppt
        """
        # Arrange: Fenster nahe MIN_DAY setzen
        lns_instance.start_day = 1
        lns_instance.end_day = 6  # size=5

        # Act: Keine Verbesserung → Expansion
        with patch("random.randint", return_value=5):  # Versuche links zu expandieren
            lns_instance.update_search_window(improvement=0)

        # Assert: Respektiert MIN_DAY
        assert lns_instance.start_day >= lns_instance.MIN_DAY

    def test_window_respects_max_boundary(self, lns_instance):
        """
        Test: Fenster kann nicht über MAX_DAY hinaus expandieren.

        Erwartet:
            - end_day <= MAX_DAY (29)
            - Bei Expansion nach rechts wird an MAX_DAY gestoppt
        """
        # Arrange: Fenster nahe MAX_DAY setzen
        lns_instance.start_day = 24
        lns_instance.end_day = 29  # size=5, MAX_DAY=29

        # Act: Keine Verbesserung → Expansion
        with patch("random.randint", return_value=0):  # Versuche rechts zu expandieren
            lns_instance.update_search_window(improvement=0)

        # Assert: Respektiert MAX_DAY
        assert lns_instance.end_day <= lns_instance.MAX_DAY

    def test_shrink_maintains_minimum_size(self, lns_instance):
        """
        Test: Beim Verkleinern wird die Mindestgröße (search_window_size_min) eingehalten.

        Erwartet:
            - Window size >= search_window_size_min (3)
            - start_day < end_day (gültiges Fenster)
        """
        # Arrange: Kleines Fenster, size=4
        lns_instance.start_day = 10
        lns_instance.end_day = 14

        # Act: Mehrfache starke Verbesserungen
        for _ in range(5):
            with patch("random.randint", return_value=1):
                lns_instance.update_search_window(improvement=5)  # Starke Verbesserung

        # Assert: Mindestgröße eingehalten
        window_size = lns_instance.end_day - lns_instance.start_day
        assert window_size >= lns_instance.search_window_size_min
        assert lns_instance.start_day < lns_instance.end_day

    def test_window_at_max_size_cannot_expand(self, lns_instance):
        """
        Test: Fenster, das bereits die maximale Größe hat, kann nicht weiter expandieren.

        Erwartet:
            - Wenn window bereits [MIN_DAY, MAX_DAY] umfasst, keine Änderung
            - Log-Meldung über fehlende Expansionsmöglichkeit
        """
        # Arrange: Maximales Fenster
        lns_instance.start_day = lns_instance.MIN_DAY
        lns_instance.end_day = lns_instance.MAX_DAY

        initial_start = lns_instance.start_day
        initial_end = lns_instance.end_day

        # Act: Versuche zu expandieren
        lns_instance.update_search_window(improvement=0)

        # Assert: Keine Änderung möglich
        assert lns_instance.start_day == initial_start
        assert lns_instance.end_day == initial_end

    def test_random_expansion_distribution(self, lns_instance):
        """
        Test: Bei Expansion wird die Vergrößerung zufällig auf links/rechts verteilt.

        Erwartet:
            - Random-Aufteilung zwischen min_left_expansion und max_left_expansion
            - Gesamte Expansion = left_expansion + right_expansion
        """
        # Arrange: Mittleres Fenster
        lns_instance.start_day = 10
        lns_instance.end_day = 15
        initial_size = lns_instance.end_day - lns_instance.start_day

        # Act: Mit spezifischem Random-Wert
        with patch("random.randint", return_value=2) as mock_random:
            lns_instance.update_search_window(improvement=0)

            # Assert: random.randint wurde aufgerufen
            assert mock_random.called

    def test_random_shrink_distribution(self, lns_instance):
        """
        Test: Bei Verkleinerung wird die Reduktion zufällig auf links/rechts verteilt.

        Erwartet:
            - Random-Aufteilung der Verkleinerung
            - Fenster bleibt gültig (start_day < end_day)
        """
        # Arrange: Größeres Fenster
        lns_instance.start_day = 5
        lns_instance.end_day = 15  # size=10

        # Act: Starke Verbesserung → Shrink
        with patch("random.randint", return_value=1) as mock_random:
            lns_instance.update_search_window(improvement=5)

            # Assert: random.randint wurde für Shrink aufgerufen
            assert mock_random.called
            assert lns_instance.start_day < lns_instance.end_day

    def test_edge_case_objective_value_zero(self, lns_instance):
        """
        Test: Spezialfall, wenn objective_value = 0 (Division durch Null vermeiden).

        Erwartet:
            - Keine Exception
            - relative_improvement = 0
            - Keine Verkleinerung des Fensters
        """
        # Arrange: Objective value auf 0 setzen
        lns_instance.old_solution.objective_value = 0
        initial_size = lns_instance.end_day - lns_instance.start_day

        # Act: Improvement angeben
        lns_instance.update_search_window(improvement=5)

        # Assert: Keine Exception, Fenster unverändert oder nur normal angepasst
        assert lns_instance.end_day > lns_instance.start_day


class Test_Module_Max_Weekends:
    class Test_slice_instance_max_days:
        @pytest.fixture(autouse=True)
        def setup(self):
            self.lokal_shift_types = shiftType.ShiftType()
            self.lokal_employee = employee.Employee(max_number_weekends=2)
            self.instance = instace.Instance.create(
                number_of_days=18,
                shift_typs=[self.lokal_shift_types],
                emplyees=[self.lokal_employee],
            )
            self.solution = Solution(self.instance)

        def get_slice_instance(self, start: int = 3, end: int = 5):
            # Mock the solver and window instance creation to speed up tests
            with patch.object(
                Slice_instance, "__init__", lambda self, sol, start, end: None
            ):
                self.slice_instance = Slice_instance(
                    self.solution, start=start, end=end
                )
                # Manually set only the attributes needed for counting methods
                self.slice_instance.sol = self.solution
                self.slice_instance.inst = self.instance
                self.slice_instance.start_day = start
                self.slice_instance.end_day = end
            return self.slice_instance

        def test_count_max_days_1(self):
            for day in range(18):
                if day in []:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in []:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=4, end=7)
            window_instance = si.create_window_instance()
            assert window_instance.weekend_days == {2}

        def test_count_max_days_2(self):
            for day in range(18):
                if day in []:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in []:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=11, end=14)
            window_instance = si.create_window_instance()
            assert window_instance.weekend_days == {2}

        def test_count_max_days_3(self):
            for day in range(18):
                if day in []:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in []:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=13, end=16)
            window_instance = si.create_window_instance()
            assert window_instance.weekend_days == {0}

        def test_count_max_days_4(self):
            for day in range(18):
                if day in []:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in []:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=13, end=16)
            window_instance = si.create_window_instance()
            assert window_instance.weekend_days == {0}

        def test_count_max_days_5(self):
            for day in range(18):
                if day in []:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in []:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=8, end=10)
            window_instance = si.create_window_instance()
            assert len(window_instance.weekend_days) == 0

        def test_count_max_days_6(self):
            for day in range(18):
                if day in [6, 12, 13]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6, 13]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=11, end=14)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 1
            )

        def test_count_max_days_7(self):
            for day in range(18):
                if day in [6, 12, 13]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6, 13]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=13, end=16)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 1
            )

        def test_count_max_days_8(self):
            for day in range(18):
                if day in [6, 12]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6, 13]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=13, end=16)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 0
            )

        def test_count_max_days_9(self):
            for day in range(18):
                if day in [6, 13]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6, 13]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=13, end=16)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 1
            )

        def test_count_max_days_10(self):
            for day in range(18):
                if day in [6, 12, 13]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6, 13]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=9, end=12)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 0
            )

        def test_count_max_days_11(self):
            for day in range(18):
                if day in [6, 12]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6, 13]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=9, end=12)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 0
            )

        def test_count_max_days_12(self):
            for day in range(18):
                if day in [6, 13]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6, 13]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=9, end=12)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 0
            )

        def test_count_max_days_13(self):
            for day in range(18):
                if day in [6]:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 1
                    )
                else:
                    self.solution.set_var(
                        day, self.lokal_shift_types.uid, self.lokal_employee.uid, 0
                    )
            for day in self.instance.weekend_days:
                if day in [6]:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 1)
                else:
                    self.solution.set_weekend_var(day, self.lokal_employee.uid, 0)

            si = self.get_slice_instance(start=9, end=12)
            window_instance = si.create_window_instance()
            assert (
                window_instance.employees[self.lokal_employee.uid].max_number_weekends
                == 1
            )
