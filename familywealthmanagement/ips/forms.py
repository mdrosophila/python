import re

from django import forms

from .models import Investor, InvestmentPolicyStatement


class InvestorForm(forms.ModelForm):
    """Name, email, phone and mailing address of an investor."""
    phone = forms.CharField(max_length=25)

    class Meta:
        model = Investor
        fields = ['name', 'email', 'phone', 'mailing_address']
        labels = {'name': 'Full name'}
        widgets = {'mailing_address': forms.Textarea(attrs={'rows': 3})}

    def clean_email(self):
        return self.cleaned_data['email'].lower()

    def clean_phone(self):
        raw = self.cleaned_data['phone']
        digits = re.sub(r'\D', '', raw)
        if not 7 <= len(digits) <= 15:
            raise forms.ValidationError('Enter a valid phone number.')
        return ('+' if raw.strip().startswith('+') else '') + digits


class IPSForm(forms.ModelForm):
    class Meta:
        model = InvestmentPolicyStatement
        exclude = ['investor', 'created_at', 'updated_at']
        widgets = {f: forms.Textarea(attrs={'rows': 3}) for f in [
            'risk_notes', 'return_notes', 'tax_considerations', 'time_horizon_notes',
            'legal_requirements', 'liquidity_needs']}

    def clean(self):
        cleaned = super().clean()
        for field in ('max_acceptable_loss_pct', 'required_return_pct', 'tax_bracket_pct', 'liquidity_reserve_pct'):
            value = cleaned.get(field)
            if value is not None and not 0 <= value <= 100:
                self.add_error(field, 'Enter a percentage between 0 and 100.')
        return cleaned
