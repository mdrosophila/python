from django.shortcuts import render

from .services.return_by_year import ASSET_COLUMNS, PERIODS, get_annualized_returns, get_statistics


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

    data = get_annualized_returns(years)
    data['series'] = {name: data['series'][name] for name in selected}
    stats = None
    if selected:
        stats = get_statistics(years, selected)
        stats['rows'] = [
            {'asset': a, 'mean': stats['mean'][a], 'sigma': stats['sigma'][a], 'beta': stats['beta'][a]}
            for a in selected
        ]
    return render(request, 'benchmark/annualized_return.html', {
        'years': years,
        'periods': PERIODS,
        'assets': assets,
        'selected': selected,
        'data': data,
        'stats': stats,
        'selected_headers': selected,
    })
