"""Typer-based CLI for the stravalib client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Iterable, Sequence

import click
import typer
from pydantic import BaseModel
from requests import exceptions as requests_exceptions

from stravalib import exc, model
from stravalib.client import ActivityUploader, BatchedResultsIterator, Client
from stravalib.util import limiter

app = typer.Typer(help="Interact with Strava data via stravalib.")
auth_app = typer.Typer(help="OAuth and token utilities.")
athlete_app = typer.Typer(help="Athlete profile and statistics.")
activities_app = typer.Typer(help="Activity management and queries.")
clubs_app = typer.Typer(help="Club discovery and membership tools.")
segments_app = typer.Typer(help="Segment lookups and analytics.")
routes_app = typer.Typer(help="Route listings and stream data.")
gear_app = typer.Typer(help="Gear information.")
subscriptions_app = typer.Typer(help="Webhook subscription helpers.")

app.add_typer(auth_app, name="auth")
app.add_typer(athlete_app, name="athlete")
app.add_typer(activities_app, name="activities")
app.add_typer(clubs_app, name="clubs")
app.add_typer(segments_app, name="segments")
app.add_typer(routes_app, name="routes")
app.add_typer(gear_app, name="gear")
app.add_typer(subscriptions_app, name="subscriptions")


@dataclass
class CLIState:
    """Shared state for CLI commands."""

    client: Client | None = None
    indent: int = 2
    output_path: Path | None = None


def _get_state(ctx: typer.Context) -> CLIState:
    obj = ctx.obj
    if obj is None:
        obj = CLIState()
        ctx.obj = obj
    assert isinstance(obj, CLIState)
    return obj


def _current_context() -> typer.Context:
    return click.get_current_context()  # type: ignore[return-value]


def _build_client(
    *,
    access_token: str | None,
    refresh_token: str | None,
    token_expires: int | None,
    rate_limit: bool,
) -> Client:
    client = Client(
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires=token_expires,
        rate_limit_requests=rate_limit,
    )
    if refresh_token:
        client.refresh_token = refresh_token
    return client


def _noop_rate_limiter(_headers: dict[str, str], _method: str) -> None:
    return None


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, Path):
        return str(value)
    return value


def _prepare_result(data: Any) -> Any:
    if isinstance(data, BatchedResultsIterator):
        return [_prepare_result(item) for item in list(data)]
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if isinstance(data, ActivityUploader):
        return {
            "upload_id": data.upload_id,
            "external_id": data.external_id,
            "activity_id": data.activity_id,
            "status": data.status,
            "error": data.error,
            "photo_metadata": data.photo_metadata,
        }
    if isinstance(data, dict):
        return {key: _prepare_result(value) for key, value in data.items()}
    if isinstance(data, Sequence) and not isinstance(
        data, (str, bytes, bytearray)
    ):
        return [_prepare_result(item) for item in data]
    if isinstance(data, Iterable) and not isinstance(
        data, (str, bytes, bytearray)
    ):
        return [_prepare_result(item) for item in list(data)]
    return data


def _emit_result(ctx: typer.Context, data: Any) -> None:
    state = _get_state(ctx)
    payload = _prepare_result(data)
    text = json.dumps(payload, indent=state.indent, default=_json_default)
    if state.output_path:
        state.output_path.parent.mkdir(parents=True, exist_ok=True)
        state.output_path.write_text(f"{text}\n", encoding="utf-8")
        typer.secho(
            f"Saved response to {state.output_path}", err=True, fg="green"
        )
    else:
        typer.echo(text)


def _handle_api_errors(func):
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            return func(*args, **kwargs)
        except (
            exc.Fault,
            exc.ObjectNotFound,
            exc.AccessUnauthorized,
        ) as error:
            typer.secho(f"Strava API error: {error}", err=True, fg="red")
            raise typer.Exit(code=1) from error
        except requests_exceptions.RequestException as error:
            typer.secho(f"HTTP error: {error}", err=True, fg="red")
            raise typer.Exit(code=1) from error

    return wrapper


def _get_client() -> Client:
    ctx = _current_context()
    state = _get_state(ctx)
    if state.client is None:
        typer.secho("Strava client is not initialised.", err=True, fg="red")
        raise typer.Exit(code=1)
    return state.client


@app.callback()
def main(
    ctx: typer.Context,
    access_token: str | None = typer.Option(
        None,
        "--access-token",
        envvar="STRAVA_ACCESS_TOKEN",
        help="Short-lived Strava access token.",
    ),
    refresh_token: str | None = typer.Option(
        None,
        "--refresh-token",
        envvar="STRAVA_REFRESH_TOKEN",
        help="Refresh token used to obtain new access tokens.",
    ),
    token_expires: int | None = typer.Option(
        None,
        "--token-expires",
        envvar="STRAVA_TOKEN_EXPIRES_AT",
        help="Epoch timestamp (seconds) when current access token expires.",
    ),
    rate_limit: bool = typer.Option(
        True,
        "--rate-limit/--no-rate-limit",
        help="Enable client-side rate limiting.",
    ),
    indent: int = typer.Option(
        2,
        "--indent",
        min=0,
        max=8,
        help="Indent level for JSON output.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "-o",
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=False,
        resolve_path=True,
        help="Write JSON response to the given file path.",
    ),
) -> None:
    state = _get_state(ctx)
    state.indent = indent
    state.output_path = output_file

    if state.client is None:
        state.client = _build_client(
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires=token_expires,
            rate_limit=rate_limit,
        )
    else:
        if access_token:
            state.client.access_token = access_token
        if refresh_token:
            state.client.refresh_token = refresh_token
        if token_expires is not None:
            state.client.token_expires = token_expires
        if rate_limit:
            state.client.protocol.rate_limiter = limiter.DefaultRateLimiter()
        else:
            state.client.protocol.rate_limiter = _noop_rate_limiter


# ---------------------------------------------------------------------------
# Authentication utilities
# ---------------------------------------------------------------------------


@auth_app.command("authorization-url")
@_handle_api_errors
def auth_authorization_url(
    client_id: int = typer.Option(..., help="Strava application client id."),
    redirect_uri: str = typer.Option(
        ..., help="Redirect URI configured in Strava."
    ),
    approval_prompt: str = typer.Option(
        "auto", help="Approval prompt behaviour: auto or force."
    ),
    scope: list[str] | None = typer.Option(
        None,
        "--scope",
        "-s",
        help="Scopes to request (repeat option for multiple).",
    ),
    state_token: str | None = typer.Option(
        None, "--state", help="Opaque state value."
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    scopes = scope if scope else None
    url = client.authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        approval_prompt=approval_prompt,  # type: ignore[arg-type]
        scope=scopes,
        state=state_token,
    )
    _emit_result(ctx, {"authorization_url": url})


@auth_app.command("exchange-token")
@_handle_api_errors
def auth_exchange_token(
    client_id: int = typer.Option(..., help="Strava application client id."),
    client_secret: str = typer.Option(
        ..., help="Strava application client secret."
    ),
    code: str = typer.Option(
        ..., help="Authorization code returned from Strava."
    ),
    return_athlete: bool = typer.Option(
        False,
        "--return-athlete/--no-return-athlete",
        help="Include the athlete payload in the response.",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    result = client.exchange_code_for_token(
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        return_athlete=return_athlete,
    )
    if return_athlete:
        access_info, athlete = result
        payload = {
            "access_info": access_info,
            "athlete": _prepare_result(athlete) if athlete else None,
        }
    else:
        payload = result
    _emit_result(ctx, payload)


@auth_app.command("refresh-token")
@_handle_api_errors
def auth_refresh_token(
    client_id: int = typer.Option(..., help="Strava application client id."),
    client_secret: str = typer.Option(
        ..., help="Strava application client secret."
    ),
    refresh_token: str = typer.Option(..., help="Existing refresh token."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    info = client.refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )
    _emit_result(ctx, info)


@auth_app.command("deauthorize")
@_handle_api_errors
def auth_deauthorize() -> None:
    ctx = _current_context()
    client = _get_client()
    client.deauthorize()
    _emit_result(ctx, {"message": "Application deauthorized."})


# ---------------------------------------------------------------------------
# Athlete operations
# ---------------------------------------------------------------------------


@athlete_app.command("profile")
@_handle_api_errors
def athlete_profile() -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_athlete())


@athlete_app.command("update")
@_handle_api_errors
def athlete_update(
    city: str | None = typer.Option(None, help="City for the athlete."),
    state_region: str | None = typer.Option(
        None, "--state", help="State or region."
    ),
    country: str | None = typer.Option(None, help="Country."),
    sex: str | None = typer.Option(None, help="Gender marker."),
    weight: float | None = typer.Option(None, help="Weight in kilograms."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    athlete = client.update_athlete(
        city=city,
        state=state_region,
        country=country,
        sex=sex,
        weight=weight,
    )
    _emit_result(ctx, athlete)


@athlete_app.command("zones")
@_handle_api_errors
def athlete_zones() -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_athlete_zones())


@athlete_app.command("stats")
@_handle_api_errors
def athlete_stats(
    athlete_id: int | None = typer.Option(
        None,
        help="Optional athlete id (defaults to authenticated athlete).",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_athlete_stats(athlete_id=athlete_id))


@athlete_app.command("koms")
@_handle_api_errors
def athlete_koms(
    athlete_id: int | None = typer.Option(
        None,
        help="Athlete id (defaults to authenticated athlete).",
    ),
    limit: int | None = typer.Option(None, help="Maximum KOMs to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    target_id = athlete_id or client.get_athlete().id
    koms = client.get_athlete_koms(target_id, limit=limit)
    _emit_result(ctx, koms)


@athlete_app.command("clubs")
@_handle_api_errors
def athlete_clubs(
    limit: int | None = typer.Option(None, help="Maximum clubs to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_athlete_clubs(limit=limit))


# ---------------------------------------------------------------------------
# Activity operations
# ---------------------------------------------------------------------------


@activities_app.command("list")
@_handle_api_errors
def activities_list(
    limit: int = typer.Option(
        20, "--limit", min=1, help="Number of activities to fetch."
    ),
    before: datetime | None = typer.Option(
        None,
        "--before",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        help="Only include activities that start before this timestamp (UTC).",
    ),
    after: datetime | None = typer.Option(
        None,
        "--after",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        help="Only include activities that start after this timestamp (UTC).",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    activities = client.get_activities(before=before, after=after, limit=limit)
    _emit_result(ctx, activities)


@activities_app.command("get")
@_handle_api_errors
def activities_get(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    include_all_efforts: bool = typer.Option(
        False,
        "--include-all-efforts/--no-include-all-efforts",
        help="Request all efforts for the activity (may be slower).",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(
        ctx,
        client.get_activity(
            activity_id, include_all_efforts=include_all_efforts
        ),
    )


@activities_app.command("create")
@_handle_api_errors
def activities_create(
    name: str = typer.Option(..., help="Name of the activity."),
    start_date_local: datetime = typer.Option(
        ...,
        "--start-date",
        formats=["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        help="Local start datetime.",
    ),
    elapsed_time: int = typer.Option(..., help="Elapsed time in seconds."),
    sport_type: str | None = typer.Option(
        None, help="Sport type (preferred)."
    ),
    activity_type: str | None = typer.Option(
        None, help="Legacy activity type (deprecated by Strava)."
    ),
    description: str | None = typer.Option(None, help="Activity description."),
    distance: float | None = typer.Option(None, help="Distance in meters."),
    trainer: bool | None = typer.Option(
        None, help="Mark as trainer activity."
    ),
    commute: bool | None = typer.Option(None, help="Mark as commute."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    activity = client.create_activity(
        name=name,
        start_date_local=start_date_local,
        elapsed_time=elapsed_time,
        sport_type=sport_type,
        activity_type=activity_type,
        description=description,
        distance=distance,
        trainer=trainer,
        commute=commute,
    )
    _emit_result(ctx, activity)


@activities_app.command("update")
@_handle_api_errors
def activities_update(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    name: str | None = typer.Option(None, help="New name."),
    sport_type: str | None = typer.Option(None, help="Sport type."),
    activity_type: str | None = typer.Option(
        None, help="Legacy activity type."
    ),
    description: str | None = typer.Option(None, help="Description."),
    private: bool | None = typer.Option(None, help="Mark as private."),
    commute: bool | None = typer.Option(None, help="Mark as commute."),
    trainer: bool | None = typer.Option(None, help="Mark as trainer."),
    gear_id: int | None = typer.Option(None, help="Gear identifier."),
    device_name: str | None = typer.Option(None, help="Device name."),
    hide_from_home: bool | None = typer.Option(None, help="Mute activity."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    activity = client.update_activity(
        activity_id=activity_id,
        name=name,
        sport_type=sport_type,
        activity_type=activity_type,
        description=description,
        private=private,
        commute=commute,
        trainer=trainer,
        gear_id=gear_id,
        device_name=device_name,
        hide_from_home=hide_from_home,
    )
    _emit_result(ctx, activity)


@activities_app.command("zones")
@_handle_api_errors
def activities_zones(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_activity_zones(activity_id))


@activities_app.command("comments")
@_handle_api_errors
def activities_comments(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    markdown: bool = typer.Option(
        False,
        "--markdown/--no-markdown",
        help="Return markdown content.",
    ),
    limit: int | None = typer.Option(None, help="Maximum comments to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(
        ctx,
        client.get_activity_comments(
            activity_id, markdown=markdown, limit=limit
        ),
    )


@activities_app.command("kudos")
@_handle_api_errors
def activities_kudos(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    limit: int | None = typer.Option(None, help="Maximum kudos to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_activity_kudos(activity_id, limit=limit))


@activities_app.command("photos")
@_handle_api_errors
def activities_photos(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    size: int | None = typer.Option(None, help="Requested photo size."),
    only_instagram: bool = typer.Option(
        False,
        "--only-instagram/--all-photos",
        help="Limit to Instagram photos only.",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(
        ctx,
        client.get_activity_photos(
            activity_id, size=size, only_instagram=only_instagram
        ),
    )


@activities_app.command("laps")
@_handle_api_errors
def activities_laps(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_activity_laps(activity_id))


@activities_app.command("streams")
@_handle_api_errors
def activities_streams(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    stream_types: list[str] | None = typer.Option(
        None,
        "--stream",
        "-s",
        help="Stream types to request (repeat option).",
    ),
    resolution: str | None = typer.Option(None, help="Stream resolution."),
    series_type: str | None = typer.Option(None, help="Series type."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    streams = client.get_activity_streams(
        activity_id,
        types=stream_types or None,
        resolution=resolution,
        series_type=series_type,
    )
    _emit_result(ctx, streams)


@activities_app.command("upload")
@_handle_api_errors
def activities_upload(
    activity_file: Path = typer.Argument(
        ..., help="Path to the activity file."
    ),
    data_type: str = typer.Option(
        ..., help="File format (fit, tcx, gpx, etc.)."
    ),
    name: str | None = typer.Option(None, help="Optional name."),
    description: str | None = typer.Option(None, help="Description."),
    activity_type: str | None = typer.Option(
        None, help="Legacy activity type."
    ),
    private: bool | None = typer.Option(None, help="Mark as private."),
    external_id: str | None = typer.Option(None, help="External identifier."),
    trainer: bool | None = typer.Option(None, help="Mark as trainer."),
    commute: bool | None = typer.Option(None, help="Mark as commute."),
    poll: bool = typer.Option(
        False,
        "--poll/--no-poll",
        help="Wait for Strava to finish processing the upload.",
    ),
    timeout: float | None = typer.Option(
        None, help="Timeout in seconds when polling."
    ),
    poll_interval: float = typer.Option(
        1.0, help="Polling interval in seconds."
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    with activity_file.open("rb") as fh:
        uploader = client.upload_activity(
            fh,
            data_type=data_type,
            name=name,
            description=description,
            activity_type=activity_type,
            private=private,
            external_id=external_id,
            trainer=trainer,
            commute=commute,
        )
    if poll:
        activity = uploader.wait(timeout=timeout, poll_interval=poll_interval)
        _emit_result(ctx, {"upload": uploader, "activity": activity})
    else:
        _emit_result(ctx, uploader)


# ---------------------------------------------------------------------------
# Club operations
# ---------------------------------------------------------------------------


@clubs_app.command("get")
@_handle_api_errors
def clubs_get(
    club_id: int = typer.Argument(..., help="Club identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_club(club_id))


@clubs_app.command("members")
@_handle_api_errors
def clubs_members(
    club_id: int = typer.Argument(..., help="Club identifier."),
    limit: int | None = typer.Option(None, help="Maximum members to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_club_members(club_id, limit=limit))


@clubs_app.command("activities")
@_handle_api_errors
def clubs_activities(
    club_id: int = typer.Argument(..., help="Club identifier."),
    limit: int | None = typer.Option(
        None, help="Maximum activities to return."
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_club_activities(club_id, limit=limit))


@clubs_app.command("admins")
@_handle_api_errors
def clubs_admins(
    club_id: int = typer.Argument(..., help="Club identifier."),
    limit: int | None = typer.Option(None, help="Maximum admins to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_club_admins(club_id, limit=limit))


@clubs_app.command("join")
@_handle_api_errors
def clubs_join(
    club_id: int = typer.Argument(..., help="Club identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    client.join_club(club_id)
    _emit_result(ctx, {"message": f"Joined club {club_id}."})


@clubs_app.command("leave")
@_handle_api_errors
def clubs_leave(
    club_id: int = typer.Argument(..., help="Club identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    client.leave_club(club_id)
    _emit_result(ctx, {"message": f"Left club {club_id}."})


# ---------------------------------------------------------------------------
# Segment operations
# ---------------------------------------------------------------------------


@segments_app.command("get")
@_handle_api_errors
def segments_get(
    segment_id: int = typer.Argument(..., help="Segment identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_segment(segment_id))


@segments_app.command("effort")
@_handle_api_errors
def segments_effort(
    effort_id: int = typer.Argument(..., help="Segment effort identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_segment_effort(effort_id))


@segments_app.command("efforts")
@_handle_api_errors
def segments_efforts(
    segment_id: int = typer.Argument(..., help="Segment identifier."),
    athlete_id: int | None = typer.Option(
        None, help="Restrict to an athlete."
    ),
    start_date: datetime | None = typer.Option(
        None,
        "--start-date",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        help="Start date filter (inclusive).",
    ),
    end_date: datetime | None = typer.Option(
        None,
        "--end-date",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        help="End date filter (inclusive).",
    ),
    limit: int | None = typer.Option(None, help="Maximum efforts to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    efforts = client.get_segment_efforts(
        segment_id,
        athlete_id=athlete_id,
        start_date_local=start_date,
        end_date_local=end_date,
        limit=limit,
    )
    _emit_result(ctx, efforts)


@segments_app.command("starred")
@_handle_api_errors
def segments_starred(
    limit: int | None = typer.Option(None, help="Maximum starred segments."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_starred_segments(limit=limit))


@segments_app.command("athlete-starred")
@_handle_api_errors
def segments_athlete_starred(
    athlete_id: int = typer.Argument(..., help="Athlete identifier."),
    limit: int | None = typer.Option(None, help="Maximum starred segments."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(
        ctx, client.get_athlete_starred_segments(athlete_id, limit=limit)
    )


@segments_app.command("explore")
@_handle_api_errors
def segments_explore(
    south_lat: float = typer.Option(..., help="South latitude."),
    west_lng: float = typer.Option(..., help="West longitude."),
    north_lat: float = typer.Option(..., help="North latitude."),
    east_lng: float = typer.Option(..., help="East longitude."),
    activity_type: str | None = typer.Option(None, help="running or riding."),
    min_cat: int | None = typer.Option(None, help="Minimum climb category."),
    max_cat: int | None = typer.Option(None, help="Maximum climb category."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    segments = client.explore_segments(
        bounds=(south_lat, west_lng, north_lat, east_lng),
        activity_type=activity_type,
        min_cat=min_cat,
        max_cat=max_cat,
    )
    _emit_result(ctx, segments)


@segments_app.command("streams")
@_handle_api_errors
def segments_streams(
    segment_id: int = typer.Argument(..., help="Segment identifier."),
    stream_types: list[str] | None = typer.Option(
        None,
        "--stream",
        "-s",
        help="Stream types to request (repeat option).",
    ),
    resolution: str | None = typer.Option(None, help="Stream resolution."),
    series_type: str | None = typer.Option(None, help="Series type."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(
        ctx,
        client.get_segment_streams(
            segment_id,
            types=stream_types or None,
            resolution=resolution,
            series_type=series_type,
        ),
    )


@segments_app.command("effort-streams")
@_handle_api_errors
def segments_effort_streams(
    effort_id: int = typer.Argument(..., help="Segment effort identifier."),
    stream_types: list[str] | None = typer.Option(
        None,
        "--stream",
        "-s",
        help="Stream types to request (repeat option).",
    ),
    resolution: str | None = typer.Option(None, help="Stream resolution."),
    series_type: str | None = typer.Option(None, help="Series type."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(
        ctx,
        client.get_effort_streams(
            effort_id,
            types=stream_types or None,
            resolution=resolution,
            series_type=series_type,
        ),
    )


# ---------------------------------------------------------------------------
# Route operations
# ---------------------------------------------------------------------------


@routes_app.command("list")
@_handle_api_errors
def routes_list(
    athlete_id: int | None = typer.Option(
        None,
        help="Athlete identifier (defaults to authenticated athlete).",
    ),
    limit: int | None = typer.Option(None, help="Maximum routes to return."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_routes(athlete_id=athlete_id, limit=limit))


@routes_app.command("get")
@_handle_api_errors
def routes_get(
    route_id: int = typer.Argument(..., help="Route identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_route(route_id))


@routes_app.command("streams")
@_handle_api_errors
def routes_streams(
    route_id: int = typer.Argument(..., help="Route identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_route_streams(route_id))


# ---------------------------------------------------------------------------
# Gear operations
# ---------------------------------------------------------------------------


@gear_app.command("get")
@_handle_api_errors
def gear_get(
    gear_id: str = typer.Argument(..., help="Gear identifier."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_gear(gear_id))


# ---------------------------------------------------------------------------
# Subscription operations
# ---------------------------------------------------------------------------


@subscriptions_app.command("create")
@_handle_api_errors
def subscriptions_create(
    client_id: int = typer.Option(..., help="Application client id."),
    client_secret: str = typer.Option(..., help="Application client secret."),
    callback_url: str = typer.Option(
        ..., help="Callback URL registered with Strava."
    ),
    verify_token: str = typer.Option(
        model.Subscription.VERIFY_TOKEN_DEFAULT,
        help="Verify token to validate callback requests.",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(
        ctx,
        client.create_subscription(
            client_id=client_id,
            client_secret=client_secret,
            callback_url=callback_url,
            verify_token=verify_token,
        ),
    )


@subscriptions_app.command("list")
@_handle_api_errors
def subscriptions_list(
    client_id: int = typer.Option(..., help="Application client id."),
    client_secret: str = typer.Option(..., help="Application client secret."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.list_subscriptions(client_id, client_secret))


@subscriptions_app.command("delete")
@_handle_api_errors
def subscriptions_delete(
    subscription_id: int = typer.Argument(
        ..., help="Subscription identifier."
    ),
    client_id: int = typer.Option(..., help="Application client id."),
    client_secret: str = typer.Option(..., help="Application client secret."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    client.delete_subscription(
        subscription_id=subscription_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    _emit_result(ctx, {"message": f"Deleted subscription {subscription_id}."})


@subscriptions_app.command("challenge")
@_handle_api_errors
def subscriptions_challenge(
    payload_file: Path | None = typer.Option(
        None, help="Path to JSON payload received from Strava."
    ),
    payload: str | None = typer.Option(None, help="Raw JSON payload string."),
    verify_token: str = typer.Option(
        model.Subscription.VERIFY_TOKEN_DEFAULT,
        help="Verify token configured with Strava.",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    if payload_file:
        raw = json.loads(payload_file.read_text())
    elif payload:
        raw = json.loads(payload)
    else:
        raw = json.loads(typer.prompt("Paste the JSON payload"))
    _emit_result(
        ctx,
        client.handle_subscription_callback(raw, verify_token=verify_token),
    )


@subscriptions_app.command("process-update")
@_handle_api_errors
def subscriptions_process_update(
    payload_file: Path | None = typer.Option(
        None, help="Path to JSON update payload from Strava."
    ),
    payload: str | None = typer.Option(None, help="Raw JSON payload string."),
) -> None:
    ctx = _current_context()
    client = _get_client()
    if payload_file:
        raw = json.loads(payload_file.read_text())
    elif payload:
        raw = json.loads(payload)
    else:
        raw = json.loads(typer.prompt("Paste the JSON payload"))
    _emit_result(ctx, client.handle_subscription_update(raw))


# ---------------------------------------------------------------------------
# Backwards-compatible root commands
# ---------------------------------------------------------------------------


@app.command()
@_handle_api_errors
def whoami() -> None:
    athlete_profile()


@app.command("athlete-stats")
@_handle_api_errors
def root_athlete_stats(
    athlete_id: int | None = typer.Option(
        None,
        help="Optional athlete id (defaults to authenticated athlete).",
    ),
) -> None:
    ctx = _current_context()
    client = _get_client()
    _emit_result(ctx, client.get_athlete_stats(athlete_id=athlete_id))


@app.command("activities-recent")
@_handle_api_errors
def activities_recent(
    limit: int = typer.Option(
        20, "--limit", min=1, help="Number of activities to fetch."
    ),
    before: datetime | None = typer.Option(
        None,
        "--before",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        help="Only include activities that start before this timestamp (UTC).",
    ),
    after: datetime | None = typer.Option(
        None,
        "--after",
        formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        help="Only include activities that start after this timestamp (UTC).",
    ),
) -> None:
    activities_list(limit=limit, before=before, after=after)


@app.command("activity")
@_handle_api_errors
def root_activity(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    include_all_efforts: bool = typer.Option(
        False,
        "--include-all-efforts/--no-include-all-efforts",
        help="Request all efforts for the activity (may be slower).",
    ),
) -> None:
    activities_get(
        activity_id=activity_id, include_all_efforts=include_all_efforts
    )


@app.command("activity-streams")
@_handle_api_errors
def root_activity_streams(
    activity_id: int = typer.Argument(..., help="Activity identifier."),
    stream_types: list[str] | None = typer.Option(
        None,
        "--stream",
        "-s",
        help="Stream types to request (repeat option).",
    ),
    resolution: str | None = typer.Option(None, help="Stream resolution."),
    series_type: str | None = typer.Option(None, help="Series type."),
) -> None:
    activities_streams(
        activity_id=activity_id,
        stream_types=stream_types,
        resolution=resolution,
        series_type=series_type,
    )


@app.command("athlete-zones")
@_handle_api_errors
def root_athlete_zones() -> None:
    athlete_zones()


@app.command("athlete-clubs")
@_handle_api_errors
def root_athlete_clubs(
    limit: int | None = typer.Option(None, help="Maximum clubs to return."),
) -> None:
    athlete_clubs(limit=limit)


@app.command("segments-explore")
@_handle_api_errors
def root_segments_explore(
    south_lat: float = typer.Option(..., help="South latitude."),
    west_lng: float = typer.Option(..., help="West longitude."),
    north_lat: float = typer.Option(..., help="North latitude."),
    east_lng: float = typer.Option(..., help="East longitude."),
    activity_type: str | None = typer.Option(None, help="running or riding."),
    min_cat: int | None = typer.Option(None, help="Minimum climb category."),
    max_cat: int | None = typer.Option(None, help="Maximum climb category."),
) -> None:
    segments_explore(
        south_lat=south_lat,
        west_lng=west_lng,
        north_lat=north_lat,
        east_lng=east_lng,
        activity_type=activity_type,
        min_cat=min_cat,
        max_cat=max_cat,
    )


def main_entry() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main_entry()
