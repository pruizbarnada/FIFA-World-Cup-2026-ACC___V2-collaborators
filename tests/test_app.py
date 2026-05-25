import os
import tempfile
import unittest
from pathlib import Path


_TEST_DB_DIR = tempfile.TemporaryDirectory()
os.environ["DB_PATH"] = str(Path(_TEST_DB_DIR.name) / "predictions.db")
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ALLOWED_EMAILS_PATH"] = str(Path(_TEST_DB_DIR.name) / "allowed_emails.txt")

import app as app_module  # noqa: E402


def tearDownModule():
    _TEST_DB_DIR.cleanup()


class ScoringTests(unittest.TestCase):
    def test_no_points_before_results_exist(self):
        picks = {
            "groups": {"A": {"first": "Mexico", "second": "Korea", "third": "Czechia"}},
            "ko": {"r32": {"0": {"winner": "Mexico", "homeScore": 2, "awayScore": 1}}},
        }

        self.assertEqual(app_module.calculate_score(picks), 0)
        self.assertEqual(app_module.calculate_score(picks, {}), 0)
        self.assertEqual(app_module.calculate_score(picks, None), 0)

    def test_group_placement_points(self):
        picks = {
            "groups": {
                "A": {"first": "Mexico", "second": "Korea", "third": "Czechia"},
                "B": {"first": "Canada", "second": "Switzerland"},
            }
        }
        results = {
            "groups": {
                "A": {"first": "Mexico", "second": "Czechia", "third": "Korea"},
                "B": {"first": "Switzerland", "second": "Canada"},
            }
        }

        # Group A: only 1st correct (3). Group B: no exact matches (0).
        self.assertEqual(app_module.calculate_score(picks, results), 3)

    def test_thirds_ranking_exact_and_advance(self):
        picks = {
            "thirds_ranking": ["Brazil", "Germany", "Spain", "Italy", "England", "France", "Argentina", "Belgium"],
        }
        results = {
            "thirds_advancing": ["Brazil", "Spain", "Germany", "Argentina"],
        }

        # Brazil at idx 0 exact = 1 (advance) + 1 (exact) = 2.
        # Germany advances but not at idx 1 = 1.
        # Spain advances but not at idx 2 (Spain is idx 1 in actual) = 1.
        # Argentina advances but not at idx 6 = 1.
        self.assertEqual(app_module.calculate_score(picks, results), 5)

    def test_ko_winner_and_score_bonus(self):
        picks = {
            "ko": {
                "r32": {
                    "0": {"winner": "Mexico", "homeScore": 2, "awayScore": 1},
                    "1": {"winner": "Brazil", "homeScore": 1, "awayScore": 0},
                }
            }
        }
        results = {
            "ko": {
                "r32": {
                    "0": {"winner": "Mexico", "homeScore": 2, "awayScore": 1},
                    "1": {"winner": "Brazil", "homeScore": 3, "awayScore": 2},
                }
            }
        }
        # Mexico winner (3) + correct score bonus (5) + Brazil winner (3) = 11
        self.assertEqual(app_module.calculate_score(picks, results), 11)

    def test_ko_wrong_winner_no_points(self):
        picks = {"ko": {"r32": {"0": {"winner": "Mexico", "homeScore": 2, "awayScore": 1}}}}
        results = {"ko": {"r32": {"0": {"winner": "Brazil", "homeScore": 2, "awayScore": 1}}}}
        self.assertEqual(app_module.calculate_score(picks, results), 0)

    def test_invalid_score_value_drops_bonus(self):
        picks = {
            "ko": {
                "r32": {
                    "0": {"winner": "Mexico", "homeScore": 31, "awayScore": 1},
                    "1": {"winner": "Brazil", "homeScore": "2", "awayScore": 0},
                }
            }
        }
        results = {
            "ko": {
                "r32": {
                    "0": {"winner": "Mexico", "homeScore": 31, "awayScore": 1},
                    "1": {"winner": "Brazil", "homeScore": 2, "awayScore": 0},
                }
            }
        }
        # Mexico picked correctly (+3), invalid pick score → no bonus.
        # Brazil picked correctly (+3), string pick score → no bonus.
        self.assertEqual(app_module.calculate_score(picks, results), 6)

    def test_full_round_points_map(self):
        picks = {
            "ko": {
                "r32": {"0": {"winner": "A"}},
                "r16": {"0": {"winner": "B"}},
                "qf": {"0": {"winner": "C"}},
                "sf": {"0": {"winner": "D"}},
                "f": {"0": {"winner": "E"}},
            }
        }
        results = {
            "ko": {
                "r32": {"0": {"winner": "A"}},
                "r16": {"0": {"winner": "B"}},
                "qf": {"0": {"winner": "C"}},
                "sf": {"0": {"winner": "D"}},
                "f": {"0": {"winner": "E"}},
            }
        }
        # 3 + 5 + 8 + 12 + 20 = 48
        self.assertEqual(app_module.calculate_score(picks, results), 48)


class ResultsApiTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        if app_module.DB_PATH.exists():
            app_module.DB_PATH.unlink()
        app_module.init_db()
        self.client = app_module.app.test_client()

    def _login_admin(self):
        os.environ["ADMIN_PASSWORD"] = "secret"
        with self.client.session_transaction() as sess:
            sess["is_admin"] = True

    def test_get_results_returns_empty_when_unset(self):
        resp = self.client.get("/api/results")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["ok"])
        self.assertFalse(body["has_results"])
        self.assertEqual(body["results"], {})

    def test_set_results_requires_admin(self):
        resp = self.client.post("/admin/results", json={"results": {}})
        self.assertEqual(resp.status_code, 401)

    def test_set_results_recalculates_scores(self):
        self._login_admin()
        save_resp = self.client.post(
            "/api/save",
            json={
                "email": "till@example.com",
                "name": "Till",
                "picks": {
                    "groups": {"A": {"first": "Mexico"}},
                    "ko": {"r32": {"0": {"winner": "Mexico"}}},
                },
            },
        )
        self.assertEqual(save_resp.status_code, 200)
        self.assertEqual(save_resp.get_json()["score"], 0)

        results_resp = self.client.post(
            "/admin/results",
            json={
                "results": {
                    "groups": {"A": {"first": "Mexico"}},
                    "ko": {"r32": {"0": {"winner": "Mexico"}}},
                }
            },
        )
        self.assertEqual(results_resp.status_code, 200)
        self.assertEqual(results_resp.get_json()["recalculated"], 1)

        leaderboard = self.client.get("/api/leaderboard").get_json()
        self.assertEqual(leaderboard["entries"][0]["score"], 6)


class SavePicksTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        if app_module.DB_PATH.exists():
            app_module.DB_PATH.unlink()
        app_module.init_db()
        self.client = app_module.app.test_client()

    def test_save_rejects_invalid_email(self):
        response = self.client.post(
            "/api/save",
            json={"email": "not-an-email", "name": "Till", "picks": {}},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "A valid email address is required.")

    def test_save_scores_zero_without_results(self):
        response = self.client.post(
            "/api/save",
            json={
                "email": "till@example.com",
                "name": "Till",
                "picks": {
                    "ko": {
                        "r32": {
                            "0": {"winner": "Brazil", "homeScore": 2, "awayScore": 1},
                            "1": {"winner": "Argentina", "homeScore": 1, "awayScore": 0},
                        }
                    }
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["score"], 0)


class PicksLockTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        if app_module.DB_PATH.exists():
            app_module.DB_PATH.unlink()
        app_module.init_db()
        self.client = app_module.app.test_client()
        self._orig_lock_at = app_module.PICKS_LOCK_AT

    def tearDown(self):
        app_module.PICKS_LOCK_AT = self._orig_lock_at

    def _set_lock(self, iso: str) -> None:
        app_module.PICKS_LOCK_AT = iso

    def test_save_before_lock_accepts_group_picks(self):
        self._set_lock("2999-01-01T00:00:00+00:00")
        resp = self.client.post(
            "/api/save",
            json={
                "email": "till@example.com",
                "name": "Till",
                "picks": {"groups": {"A": {"first": "Mexico"}}, "thirds_ranking": ["Mexico"]},
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.get_json()["locked"])

    def test_save_after_lock_preserves_stored_groups_and_thirds(self):
        # Submit before the deadline with real group + thirds data.
        self._set_lock("2999-01-01T00:00:00+00:00")
        self.client.post(
            "/api/save",
            json={
                "email": "till@example.com",
                "name": "Till",
                "picks": {
                    "groups": {"A": {"first": "Mexico"}},
                    "thirds_ranking": ["Mexico"],
                    "ko": {"r32": {"0": {"winner": "Mexico"}}},
                },
            },
        )

        # After the deadline, an attempt to overwrite groups/thirds is ignored,
        # but KO picks still update.
        self._set_lock("2000-01-01T00:00:00+00:00")
        resp = self.client.post(
            "/api/save",
            json={
                "email": "till@example.com",
                "name": "Till",
                "picks": {
                    "groups": {"A": {"first": "Brazil"}},
                    "thirds_ranking": ["Brazil"],
                    "ko": {"r32": {"0": {"winner": "Argentina"}}},
                },
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["locked"])

        stored = self.client.get("/api/picks/till@example.com").get_json()["picks"]
        self.assertEqual(stored["groups"], {"A": {"first": "Mexico"}})
        self.assertEqual(stored["thirds_ranking"], ["Mexico"])
        self.assertEqual(stored["ko"]["r32"]["0"]["winner"], "Argentina")


class PodiumScoringTests(unittest.TestCase):
    def test_podium_exact_match_scores_10_6_4(self):
        picks = {"podium": {"first": "Brazil", "second": "France", "third": "Argentina"}}
        results = {"podium": {"first": "Brazil", "second": "France", "third": "Argentina"}}
        self.assertEqual(app_module.calculate_score(picks, results), 20)

    def test_partial_podium_scores_partial(self):
        picks = {"podium": {"first": "Brazil", "second": "France", "third": "Argentina"}}
        results = {"podium": {"first": "Brazil", "second": "Spain", "third": "Argentina"}}
        # 10 (first) + 0 + 4 (third)
        self.assertEqual(app_module.calculate_score(picks, results), 14)

    def test_legacy_champion_field_still_counts(self):
        picks = {"champion": "Brazil"}
        results = {"podium": {"first": "Brazil"}}
        self.assertEqual(app_module.calculate_score(picks, results), 10)

    def test_podium_without_results_is_zero(self):
        picks = {"podium": {"first": "Brazil", "second": "France", "third": "Argentina"}}
        self.assertEqual(app_module.calculate_score(picks, {}), 0)

    def test_fourth_place_scores_three_points(self):
        picks = {
            "podium": {"first": "Brazil", "second": "France", "third": "Argentina", "fourth": "Spain"}
        }
        results = {
            "podium": {"first": "Brazil", "second": "France", "third": "Argentina", "fourth": "Spain"}
        }
        # 10 + 6 + 4 + 3
        self.assertEqual(app_module.calculate_score(picks, results), 23)

    def test_fourth_place_alone_scores_three(self):
        picks = {"podium": {"first": "Mexico", "second": "Canada", "third": "USA", "fourth": "Spain"}}
        results = {"podium": {"first": "Brazil", "second": "France", "third": "Argentina", "fourth": "Spain"}}
        self.assertEqual(app_module.calculate_score(picks, results), 3)


class TeamPickerTests(unittest.TestCase):
    def test_rejects_club_team_for_country_query(self):
        teams = [
            {"idTeam": "133604", "strTeam": "Arsenal", "strLeague": "English Premier League",
             "strSport": "Soccer", "strCountry": "England"},
            {"idTeam": "133619", "strTeam": "Chelsea", "strLeague": "English Premier League",
             "strSport": "Soccer", "strCountry": "England"},
        ]
        self.assertIsNone(app_module._pick_national_team(teams, "england"))

    def test_picks_national_team_when_present(self):
        teams = [
            {"idTeam": "133604", "strTeam": "Arsenal", "strLeague": "English Premier League",
             "strSport": "Soccer", "strCountry": "England"},
            {"idTeam": "133619", "strTeam": "England", "strLeague": "",
             "strSport": "Soccer", "strCountry": "England"},
        ]
        chosen = app_module._pick_national_team(teams, "england")
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["strTeam"], "England")

    def test_picks_national_team_when_international_league(self):
        teams = [
            {"idTeam": "999", "strTeam": "Brazil", "strLeague": "International Friendlies",
             "strSport": "Soccer", "strCountry": "Brazil"},
        ]
        chosen = app_module._pick_national_team(teams, "brazil")
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["strTeam"], "Brazil")

    def test_ignores_non_soccer_teams(self):
        teams = [
            {"idTeam": "1", "strTeam": "England", "strLeague": "Cricket League",
             "strSport": "Cricket", "strCountry": "England"},
        ]
        self.assertIsNone(app_module._pick_national_team(teams, "england"))


class FootballDataParserTests(unittest.TestCase):
    def test_parses_group_standings_and_ko_winners(self):
        matches = [
            {
                "status": "FINISHED",
                "stage": "GROUP_STAGE",
                "group": "GROUP_A",
                "homeTeam": {"name": "Mexico"},
                "awayTeam": {"name": "South Korea"},
                "score": {"fullTime": {"home": 2, "away": 0}},
            },
            {
                "status": "FINISHED",
                "stage": "GROUP_STAGE",
                "group": "GROUP_A",
                "homeTeam": {"name": "South Africa"},
                "awayTeam": {"name": "Czechia"},
                "score": {"fullTime": {"home": 1, "away": 1}},
            },
            {
                "status": "FINISHED",
                "stage": "ROUND_OF_32",
                "homeTeam": {"name": "Mexico"},
                "awayTeam": {"name": "Canada"},
                "score": {"winner": "HOME_TEAM", "fullTime": {"home": 3, "away": 1}},
            },
            {
                "status": "SCHEDULED",
                "stage": "ROUND_OF_16",
                "homeTeam": {"name": "Mexico"},
                "awayTeam": {"name": "Brazil"},
                "score": {"winner": None, "fullTime": {"home": None, "away": None}},
            },
        ]

        out = app_module.parse_football_data_results(matches)
        self.assertEqual(out["groups"]["A"]["first"], "Mexico")
        self.assertEqual(out["ko"]["r32"]["0"]["winner"], "Mexico")
        self.assertEqual(out["ko"]["r32"]["0"]["homeScore"], 3)
        self.assertEqual(out["ko"]["r16"], {})


if __name__ == "__main__":
    unittest.main()
