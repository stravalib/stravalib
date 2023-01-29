======================================================
Limiter - in Utility Submodule: Functions and Classes
======================================================
.. currentmodule:: stravalib.util.limiter

This module provides a mixture of helpers to support rate limiting
and also functions for conversion?

**TODO:** look into whether total_seconds relates to limiter actions or
unit conversion

Summary Functions
-------------------------------
.. autosummary::
   :toctree: api/

   total_seconds
   get_rates_from_response_headers
   get_seconds_until_next_quarter
   get_seconds_until_next_day


Summary Classes
-------------------------------
.. autosummary::
   :toctree: api/

   XRateLimitRule
   SleepingRateLimitRule
   RateLimitRule
   RateLimiter
   DefaultRateLimiter
