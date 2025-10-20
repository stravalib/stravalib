from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel
from typer.testing import CliRunner

import stravalib.cli as cli
from stravalib import exc


class FakeAthlete(BaseModel):
    id: int
    firstname: str


class FakeActivity(BaseModel):
    id: int
    name: str


class FakeStats(BaseModel):
    biggest_ride_distance: int


class FakeSegment(BaseModel):
    id: int
    name: str


class FakeGear(BaseModel):
    id: str
    name: str


class StubUploader:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.upload_id = 404
        self.external_id = "upload.fit"
        self.activity_id: int | None = None
        self.status = "processing"
        self.error: str | None = None
        self._photo_metadata: Any = None

    @property
    def photo_metadata(self) -> Any:
        return self._photo_metadata

    @photo_metadata.setter
    def photo_metadata(self, value: Any) -> None:
        self._photo_metadata = value

    def wait(self, *_args: Any, **_kwargs: Any) -> FakeActivity:
        self.activity_id = 555
        return FakeActivity(id=555, name="Polled Activity")


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expires: int | None = None
        self.protocol = SimpleNamespace(rate_limiter="original")

    def _record(self, action: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((action, args, kwargs))

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def authorization_url(self, *args: Any, **kwargs: Any) -> str:
        self._record("authorization_url", *args, **kwargs)
        return "https://example.com/auth"

    def exchange_code_for_token(self, *args: Any, **kwargs: Any) -> Any:
        self._record("exchange_code_for_token", *args, **kwargs)
        info = {"access_token": "tok", "refresh_token": "ref", "expires_at": 1}
        if kwargs.get("return_athlete"):
            return info, FakeAthlete(id=7, firstname="Tester")
        return info

    def refresh_access_token(
        self, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        self._record("refresh_access_token", *args, **kwargs)
        return {"access_token": "tok", "refresh_token": "ref", "expires_at": 2}

    def deauthorize(self) -> None:
        self._record("deauthorize")

    # ------------------------------------------------------------------
    # Athlete
    # ------------------------------------------------------------------
    def get_athlete(self) -> FakeAthlete:
        self._record("get_athlete")
        return FakeAthlete(id=101, firstname="Unit")

    def update_athlete(self, **kwargs: Any) -> FakeAthlete:
        self._record("update_athlete", **kwargs)
        return FakeAthlete(id=101, firstname="Unit")

    def get_athlete_zones(self) -> dict[str, Any]:
        self._record("get_athlete_zones")
        return {"heartrate": []}

    def get_athlete_stats(self, athlete_id: int | None = None) -> FakeStats:
        self._record("get_athlete_stats", athlete_id)
        return FakeStats(biggest_ride_distance=42)

    def get_athlete_koms(
        self, athlete_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_athlete_koms", athlete_id, limit)
        return [{"id": 1}]

    def get_athlete_clubs(
        self, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_athlete_clubs", limit)
        return [{"id": 2}]

    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------
    def get_activities(self, **kwargs: Any) -> list[FakeActivity]:
        self._record("get_activities", **kwargs)
        return [FakeActivity(id=202, name="Ride")]

    def get_activity(
        self, activity_id: int, include_all_efforts: bool = False
    ) -> FakeActivity:
        self._record("get_activity", activity_id, include_all_efforts)
        return FakeActivity(id=activity_id, name="Detailed")

    def create_activity(self, **kwargs: Any) -> FakeActivity:
        self._record("create_activity", **kwargs)
        return FakeActivity(id=303, name="Created")

    def update_activity(self, activity_id: int, **kwargs: Any) -> FakeActivity:
        self._record("update_activity", activity_id, **kwargs)
        return FakeActivity(id=activity_id, name="Updated")

    def upload_activity(self, *_args: Any, **_kwargs: Any) -> StubUploader:
        self._record("upload_activity", *_args, **_kwargs)
        return StubUploader()

    def get_activity_zones(self, activity_id: int) -> list[dict[str, Any]]:
        self._record("get_activity_zones", activity_id)
        return [{"type": "heartrate"}]

    def get_activity_comments(
        self, *args: Any, **kwargs: Any
    ) -> list[dict[str, Any]]:
        self._record("get_activity_comments", *args, **kwargs)
        return [{"text": "Nice ride"}]

    def get_activity_kudos(
        self, *args: Any, **kwargs: Any
    ) -> list[dict[str, Any]]:
        self._record("get_activity_kudos", *args, **kwargs)
        return [{"firstname": "Fan"}]

    def get_activity_photos(
        self, *args: Any, **kwargs: Any
    ) -> list[dict[str, Any]]:
        self._record("get_activity_photos", *args, **kwargs)
        return [{"id": "photo"}]

    def get_activity_laps(self, activity_id: int) -> list[dict[str, Any]]:
        self._record("get_activity_laps", activity_id)
        return [{"lap": 1}]

    def get_activity_streams(
        self, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        self._record("get_activity_streams", *args, **kwargs)
        return {"watts": {"type": "watts", "data": [1, 2]}}

    # ------------------------------------------------------------------
    # Clubs
    # ------------------------------------------------------------------
    def get_club(self, club_id: int) -> dict[str, Any]:
        self._record("get_club", club_id)
        return {"id": club_id}

    def get_club_members(
        self, club_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_club_members", club_id, limit)
        return [{"id": 10}]

    def get_club_activities(
        self, club_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_club_activities", club_id, limit)
        return [{"id": 20}]

    def get_club_admins(
        self, club_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_club_admins", club_id, limit)
        return [{"id": 30}]

    def join_club(self, club_id: int) -> None:
        self._record("join_club", club_id)

    def leave_club(self, club_id: int) -> None:
        self._record("leave_club", club_id)

    # ------------------------------------------------------------------
    # Segments
    # ------------------------------------------------------------------
    def get_segment(self, segment_id: int) -> FakeSegment:
        self._record("get_segment", segment_id)
        return FakeSegment(id=segment_id, name="Segment")

    def get_segment_effort(self, effort_id: int) -> dict[str, Any]:
        self._record("get_segment_effort", effort_id)
        return {"id": effort_id}

    def get_segment_efforts(
        self, *args: Any, **kwargs: Any
    ) -> list[dict[str, Any]]:
        self._record("get_segment_efforts", *args, **kwargs)
        return [{"id": 111}]

    def get_starred_segments(
        self, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_starred_segments", limit)
        return [{"id": 222}]

    def get_athlete_starred_segments(
        self, athlete_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_athlete_starred_segments", athlete_id, limit)
        return [{"id": 333}]

    def explore_segments(self, **kwargs: Any) -> list[dict[str, Any]]:
        self._record("explore_segments", **kwargs)
        return [{"id": 444}]

    def get_segment_streams(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self._record("get_segment_streams", *args, **kwargs)
        return {"latlng": {"data": []}}

    def get_effort_streams(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self._record("get_effort_streams", *args, **kwargs)
        return {"time": {"data": []}}

    # ------------------------------------------------------------------
    # Routes & Gear
    # ------------------------------------------------------------------
    def get_routes(
        self, athlete_id: int | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        self._record("get_routes", athlete_id, limit)
        return [{"id": 555}]

    def get_route(self, route_id: int) -> dict[str, Any]:
        self._record("get_route", route_id)
        return {"id": route_id}

    def get_route_streams(self, route_id: int) -> dict[str, Any]:
        self._record("get_route_streams", route_id)
        return {"distance": {"data": []}}

    def get_gear(self, gear_id: str) -> FakeGear:
        self._record("get_gear", gear_id)
        return FakeGear(id=gear_id, name="Bike")

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------
    def create_subscription(self, **kwargs: Any) -> dict[str, Any]:
        self._record("create_subscription", **kwargs)
        return {"id": 1}

    def list_subscriptions(
        self, client_id: int, client_secret: str
    ) -> list[dict[str, Any]]:
        self._record("list_subscriptions", client_id, client_secret)
        return [{"id": 2}]

    def delete_subscription(self, **kwargs: Any) -> None:
        self._record("delete_subscription", **kwargs)

    def handle_subscription_callback(
        self, raw: dict[str, Any], verify_token: str = ""
    ) -> dict[str, Any]:
        self._record("handle_subscription_callback", raw, verify_token)
        return {"hub.challenge": raw.get("hub.challenge", "")}

    def handle_subscription_update(
        self, raw: dict[str, Any]
    ) -> dict[str, Any]:
        self._record("handle_subscription_update", raw)
        return {"received": True}


runner = CliRunner()


@pytest.fixture(autouse=True)
def patch_uploader(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "ActivityUploader", StubUploader)


@pytest.fixture()
def cli_state() -> cli.CLIState:
    return cli.CLIState(client=DummyClient())


def _invoke(
    args: list[str], state: cli.CLIState, tmp_path: Path | None = None
) -> tuple[Any, DummyClient]:
    env = {}
    result = runner.invoke(cli.app, args, obj=state, env=env)
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    return data, state.client  # type: ignore[return-value]


def test_auth_commands(cli_state: cli.CLIState) -> None:
    data, client = _invoke(
        [
            "auth",
            "authorization-url",
            "--client-id",
            "123",
            "--redirect-uri",
            "http://localhost/callback",
            "--scope",
            "read",
            "--state",
            "xyz",
        ],
        cli_state,
    )
    assert data["authorization_url"].startswith("https://example.com")
    assert client.calls[-1][0] == "authorization_url"

    data, client = _invoke(
        [
            "auth",
            "exchange-token",
            "--client-id",
            "7",
            "--client-secret",
            "secret",
            "--code",
            "auth-code",
            "--return-athlete",
        ],
        cli_state,
    )
    assert data["access_info"]["access_token"] == "tok"
    assert data["athlete"]["firstname"] == "Tester"

    data, _ = _invoke(
        [
            "auth",
            "exchange-token",
            "--client-id",
            "7",
            "--client-secret",
            "secret",
            "--code",
            "auth-code",
        ],
        cli_state,
    )
    assert data["access_token"] == "tok"

    data, client = _invoke(
        [
            "auth",
            "refresh-token",
            "--client-id",
            "7",
            "--client-secret",
            "secret",
            "--refresh-token",
            "ref",
        ],
        cli_state,
    )
    assert data["refresh_token"] == "ref"

    result = runner.invoke(cli.app, ["auth", "deauthorize"], obj=cli_state)
    assert result.exit_code == 0
    assert cli_state.client.calls[-1][0] == "deauthorize"


def test_athlete_commands(cli_state: cli.CLIState, tmp_path: Path) -> None:
    data, client = _invoke(["athlete", "profile"], cli_state)
    assert data["firstname"] == "Unit"

    data, client = _invoke(
        [
            "athlete",
            "update",
            "--city",
            "Austin",
            "--state",
            "Texas",
            "--country",
            "USA",
            "--sex",
            "M",
            "--weight",
            "82.5",
        ],
        cli_state,
    )
    assert client.calls[-1][0] == "update_athlete"

    data, _ = _invoke(["athlete", "zones"], cli_state)
    assert "heartrate" in data

    data, _ = _invoke(["athlete", "stats", "--athlete-id", "99"], cli_state)
    assert data["biggest_ride_distance"] == 42

    data, _ = _invoke(
        ["athlete", "koms", "--athlete-id", "123", "--limit", "5"], cli_state
    )
    assert data[0]["id"] == 1

    data, _ = _invoke(["athlete", "clubs", "--limit", "3"], cli_state)
    assert data[0]["id"] == 2

    output_file = tmp_path / "athlete.json"
    result = runner.invoke(
        cli.app,
        ["--output-file", str(output_file), "athlete", "profile"],
        obj=cli_state,
    )
    assert result.exit_code == 0
    saved = json.loads(output_file.read_text())
    assert saved["id"] == 101


def test_activities_commands(cli_state: cli.CLIState, tmp_path: Path) -> None:
    before = "2025-01-02T00:00"
    after = "2025-01-01T00:00"
    data, client = _invoke(
        [
            "activities",
            "list",
            "--limit",
            "3",
            "--before",
            before,
            "--after",
            after,
        ],
        cli_state,
    )
    assert data[0]["id"] == 202
    assert client.calls[-1][0] == "get_activities"

    data, _ = _invoke(["activities", "get", "123"], cli_state)
    assert data["id"] == 123

    data, _ = _invoke(
        [
            "activities",
            "create",
            "--name",
            "Commute",
            "--start-date",
            "2025-03-01T07:30",
            "--elapsed-time",
            "3600",
            "--sport-type",
            "Ride",
            "--description",
            "Morning ride",
            "--distance",
            "1234",
            "--trainer",
        ],
        cli_state,
    )
    assert data["name"] == "Created"

    data, _ = _invoke(
        [
            "activities",
            "update",
            "123",
            "--name",
            "Updated",
            "--activity-type",
            "Run",
            "--private",
            "--commute",
            "--trainer",
            "--gear-id",
            "123",
            "--device-name",
            "computer",
            "--hide-from-home",
        ],
        cli_state,
    )
    assert data["name"] == "Updated"

    data, _ = _invoke(["activities", "zones", "123"], cli_state)
    assert data[0]["type"] == "heartrate"

    data, _ = _invoke(
        ["activities", "comments", "123", "--markdown"], cli_state
    )
    assert data[0]["text"] == "Nice ride"

    data, _ = _invoke(
        ["activities", "kudos", "123", "--limit", "2"], cli_state
    )
    assert data[0]["firstname"] == "Fan"

    data, _ = _invoke(
        ["activities", "photos", "123", "--size", "256", "--only-instagram"],
        cli_state,
    )
    assert data[0]["id"] == "photo"

    data, _ = _invoke(["activities", "laps", "123"], cli_state)
    assert data[0]["lap"] == 1

    data, _ = _invoke(
        [
            "activities",
            "streams",
            "123",
            "--stream",
            "watts",
            "--resolution",
            "low",
        ],
        cli_state,
    )
    assert "watts" in data

    activity_file = tmp_path / "activity.fit"
    activity_file.write_bytes(b"data")
    data, _ = _invoke(
        [
            "activities",
            "upload",
            str(activity_file),
            "--data-type",
            "fit",
            "--name",
            "Ride",
        ],
        cli_state,
    )
    assert data["upload_id"] == 404

    result = runner.invoke(
        cli.app,
        [
            "activities",
            "upload",
            str(activity_file),
            "--data-type",
            "fit",
            "--poll",
            "--timeout",
            "0.1",
            "--poll-interval",
            "0.1",
        ],
        obj=cli_state,
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["activity"]["id"] == 555


def test_club_commands(cli_state: cli.CLIState) -> None:
    data, _ = _invoke(["clubs", "get", "456"], cli_state)
    assert data["id"] == 456

    data, _ = _invoke(["clubs", "members", "456", "--limit", "3"], cli_state)
    assert data[0]["id"] == 10

    data, _ = _invoke(["clubs", "activities", "456"], cli_state)
    assert data[0]["id"] == 20

    data, _ = _invoke(["clubs", "admins", "456"], cli_state)
    assert data[0]["id"] == 30

    result = runner.invoke(cli.app, ["clubs", "join", "456"], obj=cli_state)
    assert result.exit_code == 0
    result = runner.invoke(cli.app, ["clubs", "leave", "456"], obj=cli_state)
    assert result.exit_code == 0


def test_segment_and_route_commands(cli_state: cli.CLIState) -> None:
    data, _ = _invoke(["segments", "get", "789"], cli_state)
    assert data["id"] == 789

    data, _ = _invoke(["segments", "effort", "321"], cli_state)
    assert data["id"] == 321

    data, _ = _invoke(
        [
            "segments",
            "efforts",
            "789",
            "--athlete-id",
            "5",
            "--start-date",
            "2025-04-01",
            "--end-date",
            "2025-04-02",
            "--limit",
            "2",
        ],
        cli_state,
    )
    assert data[0]["id"] == 111

    data, _ = _invoke(["segments", "starred", "--limit", "2"], cli_state)
    assert data[0]["id"] == 222

    data, _ = _invoke(
        ["segments", "athlete-starred", "5", "--limit", "2"], cli_state
    )
    assert data[0]["id"] == 333

    data, _ = _invoke(
        [
            "segments",
            "explore",
            "--south-lat",
            "29.6",
            "--west-lng",
            "-95.8",
            "--north-lat",
            "29.9",
            "--east-lng",
            "-95.1",
        ],
        cli_state,
    )
    assert data[0]["id"] == 444

    data, _ = _invoke(
        ["segments", "streams", "789", "--stream", "latlng"], cli_state
    )
    assert "latlng" in data

    data, _ = _invoke(
        ["segments", "effort-streams", "321", "--stream", "time"], cli_state
    )
    assert "time" in data

    data, _ = _invoke(
        ["routes", "list", "--athlete-id", "12", "--limit", "4"], cli_state
    )
    assert data[0]["id"] == 555

    data, _ = _invoke(["routes", "get", "12"], cli_state)
    assert data["id"] == 12

    data, _ = _invoke(["routes", "streams", "12"], cli_state)
    assert "distance" in data

    data, _ = _invoke(["gear", "get", "bike"], cli_state)
    assert data["name"] == "Bike"


def test_subscription_commands(
    cli_state: cli.CLIState, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data, _ = _invoke(
        [
            "subscriptions",
            "create",
            "--client-id",
            "1",
            "--client-secret",
            "sec",
            "--callback-url",
            "https://example.com",
            "--verify-token",
            "token",
        ],
        cli_state,
    )
    assert data["id"] == 1

    data, _ = _invoke(
        [
            "subscriptions",
            "list",
            "--client-id",
            "1",
            "--client-secret",
            "sec",
        ],
        cli_state,
    )
    assert data[0]["id"] == 2

    result = runner.invoke(
        cli.app,
        [
            "subscriptions",
            "delete",
            "9",
            "--client-id",
            "1",
            "--client-secret",
            "sec",
        ],
        obj=cli_state,
    )
    assert result.exit_code == 0

    challenge_payload = json.dumps({"hub.challenge": "abc"})
    data, _ = _invoke(
        [
            "subscriptions",
            "challenge",
            "--payload",
            challenge_payload,
            "--verify-token",
            "token",
        ],
        cli_state,
    )
    assert data["hub.challenge"] == "abc"

    update_payload = json.dumps({"id": 1})
    data, _ = _invoke(
        [
            "subscriptions",
            "process-update",
            "--payload",
            update_payload,
        ],
        cli_state,
    )
    assert data["received"] is True

    challenge_file = tmp_path / "challenge.json"
    challenge_file.write_text(json.dumps({"hub.challenge": "file"}))
    data, _ = _invoke(
        [
            "subscriptions",
            "challenge",
            "--payload-file",
            str(challenge_file),
        ],
        cli_state,
    )
    assert data["hub.challenge"] == "file"

    monkeypatch.setattr(
        cli.typer, "prompt", lambda _: '{"hub.challenge": "prompt"}'
    )
    data, _ = _invoke(["subscriptions", "challenge"], cli_state)
    assert data["hub.challenge"] == "prompt"

    update_file = tmp_path / "update.json"
    update_file.write_text(json.dumps({"id": 2}))
    data, _ = _invoke(
        [
            "subscriptions",
            "process-update",
            "--payload-file",
            str(update_file),
        ],
        cli_state,
    )
    assert data["received"] is True

    monkeypatch.setattr(cli.typer, "prompt", lambda _: '{"id": 3}')
    data, _ = _invoke(["subscriptions", "process-update"], cli_state)
    assert data["received"] is True


def test_root_aliases(cli_state: cli.CLIState) -> None:
    for command in (
        ["whoami"],
        ["athlete-stats"],
        ["athlete-zones"],
        ["athlete-clubs"],
        ["activities-recent"],
        ["activity", "12"],
        ["activity-streams", "12"],
        [
            "segments-explore",
            "--south-lat",
            "29.6",
            "--west-lng",
            "-95.8",
            "--north-lat",
            "29.9",
            "--east-lng",
            "-95.1",
        ],
    ):
        result = runner.invoke(cli.app, command, obj=cli_state)
        assert result.exit_code == 0


def test_main_initialises_state_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy = DummyClient()

    monkeypatch.setattr(cli, "_build_client", lambda **_: dummy)
    result = runner.invoke(cli.app, ["athlete", "profile"])
    assert result.exit_code == 0
    assert dummy.calls[-1][0] == "get_athlete"


def test_main_updates_existing_client(cli_state: cli.CLIState) -> None:
    client = cli_state.client
    assert client is not None
    result = runner.invoke(
        cli.app,
        [
            "--access-token",
            "newtok",
            "--refresh-token",
            "newref",
            "--token-expires",
            "321",
            "--no-rate-limit",
            "athlete",
            "profile",
        ],
        obj=cli_state,
    )
    assert result.exit_code == 0
    assert client.access_token == "newtok"
    assert client.refresh_token == "newref"
    assert client.token_expires == 321
    assert client.protocol.rate_limiter is cli._noop_rate_limiter


def test_get_client_errors_when_build_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_build_client", lambda **_: None)
    result = runner.invoke(cli.app, ["athlete", "profile"])
    assert result.exit_code == 1
    assert "not initialised" in result.stderr


def test_prepare_result_helpers(tmp_path: Path) -> None:
    iterator = cli.BatchedResultsIterator(
        entity=FakeActivity,
        result_fetcher=lambda **_: [{"id": 1, "name": "Iterator"}],
        bind_client=None,
        limit=1,
    )
    prepared = cli._prepare_result(iterator)
    assert prepared[0]["name"] == "Iterator"

    prepared_gen = cli._prepare_result((x for x in [1, 2]))
    assert prepared_gen == [1, 2]

    dt = datetime(2025, 1, 1)
    td = timedelta(seconds=30)
    sample_path = tmp_path / "sample.txt"
    assert cli._json_default(dt).startswith("2025-01-01")
    assert cli._json_default(td) == 30
    assert cli._json_default(sample_path) == str(sample_path)
    assert cli._json_default(5) == 5
    assert cli._noop_rate_limiter({}, "GET") is None


def test_build_client_factory() -> None:
    client = cli._build_client(
        access_token="tok",
        refresh_token="ref",
        token_expires=10,
        rate_limit=True,
    )
    assert client.access_token == "tok"
    assert client.refresh_token == "ref"

    secondary = cli._build_client(
        access_token=None,
        refresh_token=None,
        token_expires=None,
        rate_limit=False,
    )
    assert secondary.refresh_token is None


def test_error_handling(cli_state: cli.CLIState) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise exc.Fault("Boom")

    cli_state.client.get_athlete = boom  # type: ignore[assignment]
    result = runner.invoke(cli.app, ["athlete", "profile"], obj=cli_state)
    assert result.exit_code == 1
    assert "Strava API error" in result.stderr


def test_error_handling_http(cli_state: cli.CLIState) -> None:
    from requests import exceptions as requests_exceptions

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise requests_exceptions.RequestException("boom")

    cli_state.client.get_athlete = boom  # type: ignore[assignment]
    result = runner.invoke(cli.app, ["athlete", "profile"], obj=cli_state)
    assert result.exit_code == 1
    assert "HTTP error" in result.stderr
