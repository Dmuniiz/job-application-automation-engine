"""
Map to HTTP status codes in api/routes via global exception handlers.
"""

class DomainError(Exception):
    """Domain error base class."""


class JobFetchError(DomainError):
    """Failed to fetch job from repository (ex.: network error, timeout, parsing error)."""


class JobNotFoundError(DomainError):
    """Job not found in repository (ex.: invalid hash)."""


class ScrapingSourceError(DomainError):
    """Infrastructure error in scraping source 
    (ex.: invalid URL, invalid HTML, missing data)."""