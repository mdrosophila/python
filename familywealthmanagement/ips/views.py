from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render

from .forms import IPSForm, InvestorForm
from .models import Investor, InvestmentPolicyStatement


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
