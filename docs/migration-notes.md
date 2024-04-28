# Migration Steps

1. install bump-pydantic
    pip install bump-pydantic
2. Remove pydantic pin from pyproject.toml file dependency list
was:
dependencies = ["pint", "pytz", "arrow", "requests", "pydantic<=2.0"]
now:
dependencies = ["pint", "pytz", "arrow", "requests", "pydantic"]
3. Rerun test suite - lots of broken pydantic errors


```
➜ nox -s tests
nox > Running session tests-3.10
nox > Creating virtual environment (virtualenv) using python3.10 in .nox/tests-3-10
nox > python -m pip install '.[tests]'
nox > pytest --cov=src/stravalib --cov-report=xml:coverage.xml --cov-report=term src/stravalib/tests/unit/ src/stravalib/tests/integration/
ImportError while loading conftest '/Users/leahawasser/Documents/GitHub/stravalib/src/stravalib/tests/conftest.py'.
src/stravalib/__init__.py:1: in <module>
    from stravalib.client import Client
src/stravalib/client.py:35: in <module>
    from stravalib import exc, model, strava_model, unithelper
src/stravalib/model.py:31: in <module>
    from pydantic.datetime_parse import parse_datetime
.nox/tests-3-10/lib/python3.10/site-packages/pydantic/_migration.py:302: in wrapper
    raise PydanticImportError(f'`{import_path}` has been removed in V2.')
E   pydantic.errors.PydanticImportError: `pydantic.datetime_parse:parse_datetime` has been removed in V2.
E
E   For further information visit https://errors.pydantic.dev/2.7/u/import-error
nox > Command pytest --cov=src/stravalib --cov-report=xml:coverage.xml --cov-report=term src/stravalib/tests/unit/ src/stravalib/tests/integration/ failed with exit code 4
nox > Session tests-3.10 failed.
nox > Running session tests-3.11
nox > Creating virtual environment (virtualenv) using python3.11 in .nox/tests-3-11
nox > python -m pip install '.[tests]'
nox > pytest --cov=src/stravalib --cov-report=xml:coverage.xml --cov-report=term src/stravalib/tests/unit/ src/stravalib/tests/integration/
ImportError while loading conftest '/Users/leahawasser/Documents/GitHub/stravalib/src/stravalib/tests/conftest.py'.
src/stravalib/__init__.py:1: in <module>
    from stravalib.client import Client
src/stravalib/client.py:35: in <module>
    from stravalib import exc, model, strava_model, unithelper
src/stravalib/model.py:31: in <module>
    from pydantic.datetime_parse import parse_datetime
.nox/tests-3-11/lib/python3.11/site-packages/pydantic/_migration.py:302: in wrapper
    raise PydanticImportError(f'`{import_path}` has been removed in V2.')
E   pydantic.errors.PydanticImportError: `pydantic.datetime_parse:parse_datetime` has been removed in V2.
E
E   For further information visit https://errors.pydantic.dev/2.7/u/import-error
nox > Command pytest --cov=src/stravalib --cov-report=xml:coverage.xml --cov-report=term src/stravalib/tests/unit/ src/stravalib/tests/integration/ failed with exit code 4
nox > Session tests-3.11 failed.
nox > Running session tests-3.12
nox > Creating virtual environment (virtualenv) using python3.12 in .nox/tests-3-12
nox > python -m pip install '.[tests]'
nox > pytest --cov=src/stravalib --cov-report=xml:coverage.xml --cov-report=term src/stravalib/tests/unit/ src/stravalib/tests/integration/
ImportError while loading conftest '/Users/leahawasser/Documents/GitHub/stravalib/src/stravalib/tests/conftest.py'.
src/stravalib/__init__.py:1: in <module>
    from stravalib.client import Client
src/stravalib/client.py:35: in <module>
    from stravalib import exc, model, strava_model, unithelper
src/stravalib/model.py:31: in <module>
    from pydantic.datetime_parse import parse_datetime
.nox/tests-3-12/lib/python3.12/site-packages/pydantic/_migration.py:302: in wrapper
    raise PydanticImportError(f'`{import_path}` has been removed in V2.')
E   pydantic.errors.PydanticImportError: `pydantic.datetime_parse:parse_datetime` has been removed in V2.
E
E   For further information visit https://errors.pydantic.dev/2.7/u/import-error
nox > Command pytest --cov=src/stravalib --cov-report=xml:coverage.xml --cov-report=term src/stravalib/tests/unit/ src/stravalib/tests/integration/ failed with exit code 4
nox > Session tests-3.12 failed.
```

3. Run bump-pydantic

```
❯ bump-pydantic src/stravalib
[12:12:09] Start bump-pydantic.                                             main.py:61
           Found 25 files to process.                                       main.py:78
[12:12:20] Refactored 2 files.                                             main.py:144
           Run successfully!                                               main.py:154
(stravalib-pydantic2)
```


The bump tool will NOT handle removed items for us

# What's been removed in pydantic 2.x that we use

* pydantic.datetime_parse.parse_datetime:

Parse a datetime/int/float/string and return a datetime.datetime.

This function supports time zone offsets. When the input contains one, the output uses a timezone with a fixed offset from UTC.

Raise ValueError if the input is well formatted but not a valid datetime. Raise ValueError if the input isn't well formatted.


Options
1. ingest [code from 1.x](https://github.com/pydantic/pydantic/blob/5476a758c8ac59887dbfa3aa1c3481d0a0e20837/pydantic/datetime_parse.py) and maintain (more work for us).
2. [use dateutil library](https://dateutil.readthedocs.io/en/stable/)  - this might be the preferred option

```python
from dateutil import parser

date_string = "April 28, 2023 15:22"
parsed_date = parser.parse(date_string)
print(parsed_date)
```


## Validators

[docs here](https://docs.pydantic.dev/latest/migration/#changes-to-config)
* @validator and @root_validator are deprecated
* @root_validator has been deprecated, and should be replaced with @model_validator, which also provides new features and improvements.

### Changes in the code

| pydantic 1.x  |  pydantic 2.x |   Notes |
|---|---| --|
| `@root_validator(pre=True)` | `@model_validator(mode="before")`| ideally using `@classmethod` decorator |
| __root__:  | root:   | |
| `@validator("athlete_type", pre=True)`  |  `@field_validator("athlete_type", mode="before")` | `@validator` is now `field_validator` |
| *1 __root__: list[float] = Field(..., max_items=2, min_items=2) | __root__: list[float] = Field(..., max_length=2, min_length=2) | max_items and min_items is now max_length, min_length |
| `validator("created_at_local", allow_reuse=True)` | | |

*1 : I've read that they prefer to use `root` over `__root__`. I'm unclear as to whether that is correct? (see below)

```python
# Pydantic 1.x
class TimedZoneDistribution(BaseModel):
    """
    Stores the exclusive ranges representing zones and the time spent in each.
    """

    __root__: list[TimedZoneRange]

# Pydantic 2.x
class TimedZoneDistribution(BaseModel):
    """
    Stores the exclusive ranges representing zones and the time spent in each.
    """

    root: list[TimedZoneRange]
```
