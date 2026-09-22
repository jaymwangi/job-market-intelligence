"""Unit tests for the acquisition database composition checker."""

from app.etl.acquisition.composition import DatabaseCompositionChecker


class TestDatabaseCompositionChecker:
    def test_empty_database(self, db_session):
        checker = DatabaseCompositionChecker(db_session)

        composition = checker.get_composition(country="ZZ")

        assert composition.total_jobs == 0
        assert composition.tech_count == 0
        assert composition.non_tech_count == 0
        assert composition.unclassified_count == 0

    def test_get_composition_counts_job_types(self, db_session, create_test_jobs):
        country = "T1"

        create_test_jobs(
            count=5,
            is_tech_role=True,
            country_code=country,
            source_site="composition-counts-tech",
        )

        create_test_jobs(
            count=3,
            is_tech_role=False,
            country_code=country,
            source_site="composition-counts-non-tech",
        )

        create_test_jobs(
            count=2,
            is_tech_role=False,
            country_code=country,
            source_site="composition-counts-additional-non-tech",
        )

        checker = DatabaseCompositionChecker(db_session)

        composition = checker.get_composition(country=country)

        assert composition.total_jobs == 10
        assert composition.tech_count == 5
        assert composition.non_tech_count == 5
        assert composition.unclassified_count == 0

    def test_get_composition_excludes_unclassified_when_requested(
        self,
        db_session,
        create_test_jobs,
    ):
        country = "T2"

        create_test_jobs(
            count=4,
            is_tech_role=True,
            country_code=country,
            source_site="composition-exclude-tech",
        )

        create_test_jobs(
            count=2,
            is_tech_role=False,
            country_code=country,
            source_site="composition-exclude-non-tech",
        )

        create_test_jobs(
            count=3,
            is_tech_role=False,
            country_code=country,
            source_site="composition-exclude-additional-non-tech",
        )

        checker = DatabaseCompositionChecker(db_session)

        composition = checker.get_composition(
            country=country,
            include_unclassified=False,
        )

        assert composition.total_jobs == 9
        assert composition.tech_count == 4
        assert composition.non_tech_count == 5
        assert composition.unclassified_count == 0

    def test_get_composition_filters_by_country(
        self,
        db_session,
        create_test_jobs,
    ):
        create_test_jobs(
            count=3,
            country_code="T3",
            is_tech_role=True,
            source_site="composition-country-tech",
        )

        create_test_jobs(
            count=2,
            country_code="T3",
            is_tech_role=False,
            source_site="composition-country-non-tech",
        )

        create_test_jobs(
            count=4,
            country_code="T4",
            is_tech_role=True,
            source_site="composition-other-country",
        )

        checker = DatabaseCompositionChecker(db_session)

        composition = checker.get_composition(country="T3")

        assert composition.total_jobs == 5
        assert composition.tech_count == 3
        assert composition.non_tech_count == 2
        assert composition.unclassified_count == 0

    def test_get_tech_deficit(self, db_session, create_test_jobs):
        country = "T5"

        create_test_jobs(
            count=3,
            is_tech_role=True,
            country_code=country,
            source_site="composition-deficit-tech",
        )

        create_test_jobs(
            count=7,
            is_tech_role=False,
            country_code=country,
            source_site="composition-deficit-non-tech",
        )

        checker = DatabaseCompositionChecker(db_session)

        assert checker.get_tech_deficit(country=country) == 4

    def test_get_tech_deficit_with_country_filter(
        self,
        db_session,
        create_test_jobs,
    ):
        create_test_jobs(
            count=2,
            country_code="T6",
            is_tech_role=True,
            source_site="composition-country-deficit-tech",
        )

        create_test_jobs(
            count=5,
            country_code="T6",
            is_tech_role=False,
            source_site="composition-country-deficit-non-tech",
        )

        create_test_jobs(
            count=10,
            country_code="T7",
            is_tech_role=False,
            source_site="composition-other-deficit",
        )

        checker = DatabaseCompositionChecker(db_session)

        assert checker.get_tech_deficit(country="T6") == 3

    def test_has_reached_parity(self, db_session, create_test_jobs):
        country = "T8"

        create_test_jobs(
            count=5,
            is_tech_role=True,
            country_code=country,
            source_site="composition-parity-tech",
        )

        create_test_jobs(
            count=5,
            is_tech_role=False,
            country_code=country,
            source_site="composition-parity-non-tech",
        )

        checker = DatabaseCompositionChecker(db_session)

        assert checker.has_reached_parity(country=country) is True

    def test_has_not_reached_parity(self, db_session, create_test_jobs):
        country = "T9"

        create_test_jobs(
            count=2,
            is_tech_role=True,
            country_code=country,
            source_site="composition-no-parity-tech",
        )

        create_test_jobs(
            count=8,
            is_tech_role=False,
            country_code=country,
            source_site="composition-no-parity-non-tech",
        )

        checker = DatabaseCompositionChecker(db_session)

        assert checker.has_reached_parity(country=country) is False

    def test_has_reached_parity_with_custom_tolerance(
        self,
        db_session,
        create_test_jobs,
    ):
        country = "T0"

        create_test_jobs(
            count=52,
            is_tech_role=True,
            country_code=country,
            source_site="composition-tolerance-tech",
        )

        create_test_jobs(
            count=48,
            is_tech_role=False,
            country_code=country,
            source_site="composition-tolerance-non-tech",
        )

        checker = DatabaseCompositionChecker(db_session)

        assert (
            checker.has_reached_parity(
                country=country,
                tolerance=0.05,
            )
            is True
        )
