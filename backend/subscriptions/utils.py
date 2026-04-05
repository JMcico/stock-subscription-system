"""
Ticker validation and price lookup via django.core.cache + yfinance (or mock).
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_CACHE_PREFIX = 'stock_price:'


def _cache_key(ticker: str) -> str:
    return f"{_CACHE_PREFIX}{ticker.strip().upper()}"


def get_price(ticker: str) -> Decimal:
    """
    Read-through cache: try cache → then API (yfinance or mock random).
    TTL: settings.PRICE_CACHE_TTL (default 120s).
    """
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError('Ticker is required.')

    key = _cache_key(symbol)
    cached = cache.get(key)
    if cached is not None:
        try:
            return Decimal(str(cached))
        except (InvalidOperation, TypeError):
            pass

    if settings.YFINANCE_MOCK:
        price = round(random.uniform(10.0, 999.9999), 4)
    else:
        import yfinance as yf

        t = yf.Ticker(symbol)
        hist = t.history(period='5d')
        if hist.empty:
            raise ValueError(f'No price data available for "{symbol}".')
        price = float(hist['Close'].iloc[-1])

    cache.set(key, price, timeout=settings.PRICE_CACHE_TTL)
    return Decimal(str(price))


def _yf_has_market_data(symbol: str) -> bool:
    import yfinance as yf

    t = yf.Ticker(symbol)
    hist = t.history(period='5d')
    return not hist.empty


def _looks_like_ticker_symbol(symbol: str) -> bool:
    return bool(re.match(r'^[A-Z0-9.\-]{1,20}$', symbol))


def validate_ticker_exists(raw: str) -> str:
    """
    Ensure the symbol refers to a real listing (yfinance has recent bars).
    Returns normalized uppercase ticker.

    Raises ValueError with a user-facing message if invalid.
    """
    symbol = (raw or '').strip().upper()
    if not symbol:
        raise ValueError('Ticker is required.')

    try:
        ok = _yf_has_market_data(symbol)
    except Exception as e:
        logger.warning('yfinance error while validating %s: %s', symbol, e)
        if getattr(settings, 'YFINANCE_MOCK', False):
            if _looks_like_ticker_symbol(symbol):
                logger.info('MOCK mode: accepting ticker %s after yfinance failure', symbol)
                return symbol
        raise ValueError(
            f'Could not validate ticker "{symbol}". Try again or check your network.'
        ) from e

    if ok:
        return symbol

    if getattr(settings, 'YFINANCE_MOCK', False) and _looks_like_ticker_symbol(symbol):
        logger.warning(
            'MOCK mode: no yfinance data for %s; accepting as placeholder', symbol
        )
        return symbol

    raise ValueError(
        f'Ticker "{symbol}" is not a valid symbol or has no recent market data.'
    )


_AI_FALLBACK = {
    'signal': 'Hold',
    'reason': 'AI analysis temporarily unavailable',
}


def _parse_json_loose(text: str) -> dict | list | None:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'(\{[^{}]*\}|\[[^\[\]]*\])', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    return None


def get_ai_recommendation(ticker: str, price: Decimal) -> dict:
    """
    Single-ticker demo signal via OpenAI gpt-4o (or settings.OPENAI_MODEL).
    Returns {"signal": "Buy"|"Hold"|"Sell", "reason": str}.
    On any failure, returns the standard fallback (no exception).
    """
    out = dict(_AI_FALLBACK)
    api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.warning('OPENAI_API_KEY not configured; using AI fallback for %s', ticker)
        return out
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o')
        user_msg = (
            f'Ticker: {ticker}, last price USD: {price}. '
            'Reply with ONE JSON object only, keys: signal (Buy, Hold, or Sell), reason (one short sentence). '
            'Demo only, not financial advice.'
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You output only valid JSON objects. Keys: signal, reason.',
                },
                {'role': 'user', 'content': user_msg},
            ],
            temperature=0.25,
            max_tokens=200,
        )
        raw = (resp.choices[0].message.content or '').strip()
        parsed = _parse_json_loose(raw)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if isinstance(parsed, dict):
            sig_raw = str(parsed.get('signal', 'Hold')).strip().lower()
            if sig_raw in ('buy', 'hold', 'sell'):
                out['signal'] = sig_raw.capitalize()
            out['reason'] = str(parsed.get('reason', out['reason']))[:500]
    except Exception as e:
        logger.warning('get_ai_recommendation failed for %s: %s', ticker, e, exc_info=True)
    return out


def get_ai_recommendations_batch(
    rows: list[tuple[str, str]],
) -> list[dict]:
    """
    One OpenAI chat completion for all (ticker, price_str) rows in the same merged email.
    Returns a list of dicts with signal/reason, same length as rows (aligned by index).
    On failure, returns fallback dict per row without raising.
    """
    n = len(rows)
    fb = {'signal': 'Hold', 'reason': _AI_FALLBACK['reason']}
    if n == 0:
        return []

    api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.warning('OPENAI_API_KEY not configured; batch AI fallback')
        return [dict(fb) for _ in range(n)]

    lines = '\n'.join(f'- {t}: ${p} USD' for t, p in rows)
    prompt = (
        'For DEMO only (not financial advice). Return a JSON array only. '
        'Each element: {"ticker":"...", "signal":"Buy"|"Hold"|"Sell", "reason":"one short sentence"}. '
        'Same order as the input lines. Input:\n'
        f'{lines}'
    )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o')
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You output only a valid JSON array. No markdown fences.',
                },
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.2,
            max_tokens=min(1200, 200 + n * 80),
        )
        raw = (resp.choices[0].message.content or '').strip()
        parsed = _parse_json_loose(raw)
        if not isinstance(parsed, list):
            logger.warning('Batch AI returned non-list; using fallback')
            return [dict(fb) for _ in range(n)]

        result: list[dict] = []
        for i in range(n):
            if i < len(parsed) and isinstance(parsed[i], dict):
                sig_raw = str(parsed[i].get('signal', 'Hold')).strip().lower()
                sig = (
                    sig_raw.capitalize()
                    if sig_raw in ('buy', 'hold', 'sell')
                    else 'Hold'
                )
                result.append(
                    {
                        'signal': sig,
                        'reason': str(parsed[i].get('reason', fb['reason']))[:500],
                    }
                )
            else:
                result.append(dict(fb))
        return result
    except Exception as e:
        logger.warning('get_ai_recommendations_batch failed: %s', e, exc_info=True)
        return [dict(fb) for _ in range(n)]
