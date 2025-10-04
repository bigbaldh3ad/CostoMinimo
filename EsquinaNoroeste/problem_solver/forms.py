from django import forms
from .models import Comment


class MatrixForm(forms.Form):
    origenes = forms.IntegerField(
        min_value=1,
        label="Número de orígenes",
        widget=forms.NumberInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            }
        ),
    )
    destinos = forms.IntegerField(
        min_value=1,
        label="Número de destinos",
        widget=forms.NumberInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            }
        ),
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "placeholder": "Escribe tu observación aquí...",
                    "rows": 4,
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                }
            )
        }