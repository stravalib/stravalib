# Stravalib V2 Migration Guide

:::{toctree}
:hidden:
:caption: What's New

What's New <self>
Changelog <changelog>
:::

Stravalib V2 includes several breaking changes. The sections below provide a
guide to help you migrate your code to this
latest release.

## Pydantic V2

Stravalib now uses Pydantic V2. If your code uses extensions of Stravalib model
classes or uses Pydantic’s (de-)
serialization mechanisms such as `parse_obj()`, `dict()`, or `json()`, please
consider going
through [Pydantic’s V2 migration guide](https://docs.pydantic.dev/latest/migration/)
first.

## Legacy (de-)Serialization

The already deprecated (de-)serialization
methods `deserialize()`, `from_dict()`, and `to_dict()` are no longer
supported. Instead, please
use [Pydantic’s serialization mechanisms](https://docs.pydantic.dev/latest/concepts/serialization/).

## Strava Meta/Summary/Detailed Type Hierarchy

Many model classes were changed to reflect the type hierarchy defined in the
Strava API. This means that classes such
as `Activity` are now split into `MetaActivity`, `SummaryActivity`,
and `DetailedActivity`.
As `MetaActivity` has fewer attributes than the former `Activity` class,
this may lead to `AttributeError`s.
However, these missing attributes would have a `None` value, as the Strava API
never returned them. Code that uses
checks on `resource_state` attributes or checks attributes on being `None` to
determine the detail level of a response
object should now rely on the type itself.
Since many class names from Stravalib V1 have been replaced, any `isinstance()`
checks on Stravalib model types may
now (silently) fail.

## Unit Conversion

The former `unithelper` module is renamed to `unit_helper` for naming
consistency. The deprecated compatibility with
the `units` package is no longer supported. The helper functions
in `unit_helper` such as `feet()` or `miles()` now
return a Pint `Quantity` object.

## Custom Types

Stravalib V2 introduces new types for distances, velocities, durations, and time
zones. When accessed from a model
object. For example, `activity.distance` now returns a `Distance` type, which is an
extension of `float`. The “plain”
distance (in meters, the Strava default) can now be retrieved as a float
by `activity.distance`. However, this distance
can also be received as a `Quantity` with an explicit unit
using `activity.distance.quantity`.
This behavior differs from Stravalib V1, where `activity.distance` would
immediately return a Quantity-like object.
Detailed documentation about these new custom types can be
[found here.](custom-types-anchor)

## Other

The remaining unrelated [breaking](reference) changes are:

- The `ActivityKudos` class has been removed. Stravalib now uses the
  new `SummaryAthlete` class in its place.
- `Athlete.is_authenticated_athlete()` is removed.
- The `Bike` and `Shoe` subtypes of `Gear` are replaced
  by `strava_model.SummaryGear`.
