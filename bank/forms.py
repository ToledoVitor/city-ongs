from django import forms


class UploadOFXForm(forms.Form):
    ofx_file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "block w-full text-sm text-black border border-gray-300 rounded-lg cursor-pointer dark:text-black focus:outline-none bg-gray-300 dark:border-gray-600 dark:placeholder-gray-400"
            }
        )
    )

    def clean_ofx_file(self):
        ofx_file = self.cleaned_data.get("ofx_file")

        if ofx_file:
            if not ofx_file.name.lower().endswith(".ofx"):
                raise forms.ValidationError(
                    "Somente arquivos do tipo OFX são permitidos."
                )

            if ofx_file.size > 5 * 1024 * 1024:  # Limite de 5 MB
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 5MB."
                )

        return ofx_file

    # # Verificar o tipo MIME (opcional)
    # if ofx_file.content_type != 'application/pdf':
    #     raise forms.ValidationError("O arquivo enviado não é um OFX válido.")
