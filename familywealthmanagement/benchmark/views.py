from django.shortcuts import render

from .services.return_by_year import (
    ASSET_COLUMNS, PERIODS, get_annualized_returns, get_compound_returns, get_statistics,
    parse_lookback)


def annualized_return(request):
    try:
        years = int(request.GET.get('years', 1))
    except ValueError:
        years = 1
    if years not in PERIODS:
        years = 1

    assets = [a.strip() for a in ASSET_COLUMNS]
    if 'years' in request.GET:  # form was submitted, so an empty selection is intentional
        chosen = request.GET.getlist('asset')
        selected = [a for a in assets if a in chosen]
    else:
        selected = assets

    real = request.GET.get('basis') == 'real'
    lookback = parse_lookback(request.GET.get('lookback'))
    error = None
    if lookback is not None and lookback < years:
        error = f'The look-back ({lookback} years) must be at least the rolling period ({years} years).'
    active = [] if error else selected
    data = get_annualized_returns(years, real, lookback) if not error else {'years': [], 'series': {}}
    data['series'] = {name: data['series'][name] for name in active}
    stats = None
    if active:
        stats = get_statistics(years, active, real, lookback)
        # Compound annual return over all the data, nominal and real, for each asset.
        compound = {basis: dict(zip(assets, get_compound_returns(basis == 'real', lookback)[0]['values']))
                    for basis in ('nominal', 'real')}
        stats['period'] = get_compound_returns(False, lookback)[0]['label']
        stats['rows'] = [
            {'asset': a, 'nominal': compound['nominal'][a], 'real': compound['real'][a],
             'sigma': stats['sigma'][a], 'beta': stats['beta'][a]}
            for a in active
        ]
    return render(request, 'benchmark/annualized_return.html', {
        'years': years,
        'real': real,
        'lookback': lookback or '',
        'error': error,
        'compound_tables': {'nominal': get_compound_returns(False), 'real': get_compound_returns(True)},
        'periods': PERIODS,
        'assets': assets,
        'selected': selected,
        'data': data,
        'stats': stats,
        'selected_headers': active,
    })
