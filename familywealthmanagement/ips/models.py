from django.conf import settings
from django.db import models


class Investor(models.Model):
    """The person (user) an investment policy statement belongs to; identified by email or phone."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='investor')
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True, help_text='Digits only, with an optional leading +.')
    mailing_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} <{self.email}>'


class InvestmentPolicyStatement(models.Model):
    class RiskTolerance(models.TextChoices):
        CONSERVATIVE = 'conservative', 'Conservative'
        MODERATELY_CONSERVATIVE = 'moderately_conservative', 'Moderately conservative'
        MODERATE = 'moderate', 'Moderate'
        MODERATELY_AGGRESSIVE = 'moderately_aggressive', 'Moderately aggressive'
        AGGRESSIVE = 'aggressive', 'Aggressive'

    investor = models.ForeignKey(Investor, on_delete=models.CASCADE, related_name='policy_statements')

    # Risk tolerance
    risk_tolerance = models.CharField(max_length=30, choices=RiskTolerance.choices)
    max_acceptable_loss_pct = models.DecimalField(
        'Maximum acceptable loss in a year (%)', max_digits=5, decimal_places=2,
        help_text='Largest one-year drop you could tolerate.')
    risk_notes = models.TextField(blank=True)

    # Return requirement
    required_return_pct = models.DecimalField('Required annual return (%)', max_digits=5, decimal_places=2)
    return_notes = models.TextField('Return objective notes', blank=True)

    # Tax considerations
    tax_bracket_pct = models.DecimalField(
        'Marginal tax rate (%)', max_digits=5, decimal_places=2, null=True, blank=True)
    tax_considerations = models.TextField(blank=True, help_text='Tax-deferred accounts, capital gains, estate, etc.')

    # Time horizon
    time_horizon_years = models.PositiveIntegerField('Time horizon (years)')
    time_horizon_notes = models.TextField(blank=True, help_text='Stages or key dates, e.g. retirement, tuition.')

    # Legal and regulatory requirements
    legal_requirements = models.TextField(blank=True, help_text='Trust terms, regulations, restrictions on holdings.')

    # Liquidity needs
    liquidity_reserve_pct = models.DecimalField(
        'Liquidity reserve (% of portfolio)', max_digits=5, decimal_places=2, default=0)
    liquidity_needs = models.TextField(blank=True, help_text='Expected withdrawals, emergency funds, large expenses.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'investment policy statement'

    def __str__(self):
        return f'IPS for {self.investor.name} ({self.created_at:%Y-%m-%d})'
