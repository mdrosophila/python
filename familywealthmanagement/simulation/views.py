from django.shortcuts import render

from .services import ASSETS, data_year_range, simulate

DEFAULT_ALLOCATION = {'S&P 500 (includes dividends)': 60, 'US T. Bond (10-year)': 40}
DEFAULT_INITIAL = 10000
DEFAULT_YEARS = 20


def _number(value, default, cast=float):
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def asset_simulation(request):
    first_year, last_year = data_year_range()
    submitted = 'years' in request.GET

    years = _number(request.GET.get('years'), DEFAULT_YEARS, int)
    start = _number(request.GET.get('start'), last_year - years + 1, int)
    initial = _number(request.GET.get('initial'), DEFAULT_INITIAL)
    if submitted:
        alloc = [max(_number(request.GET.get(f'alloc_{i}'), 0.0), 0.0) for i in range(len(ASSETS))]
    else:
        alloc = [float(DEFAULT_ALLOCATION.get(a, 0)) for a in ASSETS]

    errors = []
    if years < 1:
        errors.append('Years must be at least 1.')
    if initial <= 0:
        errors.append('Starting amount must be greater than 0.')
    if start < first_year or start + years - 1 > last_year:
        errors.append(f'Historical data covers {first_year}-{last_year}, so the start year plus '
                      f'years must fit inside that range.')
    total = sum(alloc)
    if abs(total - 100) > 0.01:
        errors.append(f'Allocations must add up to 100% (currently {total:g}%).')

    result = None
    if not errors:
        weights = {a: pct / 100 for a, pct in zip(ASSETS, alloc) if pct > 0}
        result = simulate(weights, start, years, initial)

    return render(request, 'simulation/asset_simulation.html', {
        'rows': [{'index': i, 'name': a, 'pct': f'{pct:g}'} for i, (a, pct) in enumerate(zip(ASSETS, alloc))],
        'total': f'{total:g}',
        'years': years,
        'start': start,
        'initial': f'{initial:g}',
        'first_year': first_year,
        'last_year': last_year,
        'max_years': last_year - first_year + 1,
        'errors': errors,
        'result': result,
    })
