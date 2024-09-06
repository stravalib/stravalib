======================================================
Limiter - in Utility Submodule: Functions and Classes
======================================================
.. currentmodule:: stravalib.util.limiter

This module provides a mixture of helpers to support rate limiting
and also functions for conversion?

Summary Functions
-------------------------------
.. autosummary::
   :toctree: api/

   get_rates_from_response_headers
   get_seconds_until_next_quarter
   get_seconds_until_next_day


Summary Classes
-------------------------------
.. autosummary::
   :toctree: api/

   SleepingRateLimitRule
   RateLimiter
   DefaultRateLimiter
   RequestRate
