from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from benchmark.services.return_by_year import parse_lookback
from simulation.services import ASSETS, data_year_range, simulate

from .forms import IPSForm, InvestorForm
from .models import Investor, InvestmentPolicyStatement
from .portfolio import build_portfolio


def register(request):
    user_form = UserCreationForm(request.POST or None)
    investor_form = InvestorForm(request.POST or None)
    if request.method == 'POST' and user_form.is_valid() and investor_form.is_valid():
        user = user_form.save(commit=False)
        user.email = investor_form.cleaned_data['email']  # password reset emails go to this address
        user.save()
        investor = investor_form.save(commit=False)
        investor.user = user
        investor.save()
        login(request, user)
        return redirect('ips_list')
    return render(request, 'ips/register.html', {'user_form': user_form, 'investor_form': investor_form})


@login_required
def profile(request):
    investor = Investor.objects.filter(user=request.user).first()
    form = InvestorForm(request.POST or None, instance=investor)
    if request.method == 'POST' and form.is_valid():
        investor = form.save(commit=False)
        investor.user = request.user
        investor.save()
        request.user.email = investor.email
        request.user.save(update_fields=['email'])
        return redirect('ips_list')
    return render(request, 'ips/profile.html', {'form': form})


def _visible_statements(user):
    """Staff see every statement; other users only their own."""
    statements = InvestmentPolicyStatement.objects.select_related('investor')
    return statements if user.is_staff else statements.filter(investor__user=user)


@login_required
def ips_list(request):
    return render(request, 'ips/ips_list.html', {'statements': _visible_statements(request.user)})


@login_required
def ips_create(request):
    investor = Investor.objects.filter(user=request.user).first()
    if investor is None:  # the account has no investor profile yet
        return redirect('profile')
    form = IPSForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ips = form.save(commit=False)
        ips.investor = investor
        ips.save()
        return redirect('ips_detail', pk=ips.pk)
    return render(request, 'ips/ips_form.html', {'form': form, 'investor': investor})


@login_required
def ips_detail(request, pk):
    ips = get_object_or_404(_visible_statements(request.user), pk=pk)
    return render(request, 'ips/ips_detail.html', {'ips': ips})


@login_required
def ips_edit(request, pk):
    ips = get_object_or_404(_visible_statements(request.user), pk=pk)
    form = IPSForm(request.POST or None, instance=ips)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('ips_detail', pk=ips.pk)
    return render(request, 'ips/ips_form.html', {'form': form, 'investor': ips.investor, 'ips': ips, 'editing': True})


@login_required
def ips_portfolio(request, pk):
    ips = get_object_or_404(_visible_statements(request.user), pk=pk)
    try:
        initial = float(request.GET.get('initial', 100000))
    except ValueError:
        initial = 100000.0
    if initial <= 0:
        initial = 100000.0

    lookback = parse_lookback(request.GET.get('lookback'))
    portfolio = build_portfolio(ips, lookback)
    simulation = simulator_link = None
    if portfolio['weights']:
        first_year, last_year = data_year_range(lookback)
        years = min(ips.time_horizon_years, last_year - first_year + 1)
        start = last_year - years + 1
        simulation = simulate({a: pct / 100 for a, pct in portfolio['weights'].items()}, start, years, initial)
        query = {'initial': f'{initial:g}', 'start': start, 'years': years, 'lookback': lookback or ''}
        query.update({f'alloc_{i}': portfolio['weights'].get(a, 0) for i, a in enumerate(ASSETS)})
        simulator_link = f"{reverse('asset_simulation')}?{urlencode(query)}"
    return render(request, 'ips/ips_portfolio.html', {
        'ips': ips, 'portfolio': portfolio, 'result': simulation, 'initial': f'{initial:g}', 'lookback': lookback or '',
        'years': years if simulation else None, 'simulator_link': simulator_link})
