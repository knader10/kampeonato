from django import forms
from .models import Time, Jogador, Campeonato, TimeCampeonato, JogadorTimeCampeonato, Profissional, ProfissionalCampeonato, Noticia, ImagemNoticia, MidiaImagem, Patrocinio


class TimeForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ['nome', 'escudo', 'ano_fundacao', 'cidade']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'ano_fundacao': forms.NumberInput(attrs={'class': 'form-input'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input'}),
            'escudo': forms.FileInput(attrs={'class': 'form-file-input'}),
        }


class JogadorForm(forms.ModelForm):
    class Meta:
        model = Jogador
        fields = ['nome', 'data_nascimento', 'foto', 'telefone', 'cidade', 'logradouro', 
                 'bairro', 'cep', 'complemento', 'titulo_eleitor', 'zona_eleitoral', 'secao_eleitoral']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Digite o nome completo'
            }),
            'data_nascimento': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '(11) 99999-9999'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Digite a cidade'
            }),
            'logradouro': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Rua, avenida, etc.'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Digite o bairro'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '00000-000'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Apartamento, bloco, etc.'
            }),
            'titulo_eleitor': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '000000000000'
            }),
            'zona_eleitoral': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0000'
            }),
            'secao_eleitoral': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0000'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Aqui podemos filtrar times por tenant se necessário futuramente
        pass


class CampeonatoForm(forms.ModelForm):
    class Meta:
        model = Campeonato
        fields = [
            'nome', 'edicao', 'organizador', 'data_inicio', 'data_fim',
            'permite_transferencia', 'status',
            'tipo_formato', 'ida_volta',
            'num_grupos', 'num_classificados', 'observacoes_formato',
            'confrontos_mesmo_grupo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'edicao': forms.TextInput(attrs={'class': 'form-input'}),
            'organizador': forms.TextInput(attrs={'class': 'form-input'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'permite_transferencia': forms.CheckboxInput(attrs={'class': 'rounded'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'tipo_formato': forms.Select(attrs={'class': 'form-input'}),
            'ida_volta': forms.CheckboxInput(attrs={'class': 'rounded'}),
            'num_grupos': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'value': 0}),
            'num_classificados': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'value': 0}),
            'observacoes_formato': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'confrontos_mesmo_grupo': forms.CheckboxInput(attrs={'class': 'rounded'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir valores padrão para campos opcionais
        if not self.instance.pk:  # Apenas para novos objetos
            self.fields['num_grupos'].initial = 0
            self.fields['num_classificados'].initial = 0
        
        # Tornar campos opcionais para certos formatos
        self.fields['num_grupos'].required = False
        self.fields['num_classificados'].required = False

    def clean_num_grupos(self):
        """Limpeza específica para o campo num_grupos"""
        valor = self.cleaned_data.get('num_grupos')
        tipo_formato = self.data.get('tipo_formato')
        
        # Para Liga e Mata-mata, aceita valores vazios ou None
        if tipo_formato in ['liga', 'mata_mata']:
            return 0 if valor in [None, ''] else valor
        
        return valor
    
    def clean_num_classificados(self):
        """Limpeza específica para o campo num_classificados"""
        valor = self.cleaned_data.get('num_classificados')
        tipo_formato = self.data.get('tipo_formato')
        
        # Para Liga e Mata-mata, aceita valores vazios ou None
        if tipo_formato in ['liga', 'mata_mata']:
            return 0 if valor in [None, ''] else valor
        
        return valor

    def clean(self):
        cleaned_data = super().clean()
        tipo_formato = cleaned_data.get('tipo_formato')
        num_grupos = cleaned_data.get('num_grupos')
        num_classificados = cleaned_data.get('num_classificados')
        
        # Para Liga e Mata-mata, os campos de grupos não são obrigatórios
        if tipo_formato in ['liga', 'mata_mata']:
            # Define valores padrão quando os campos estão vazios ou None
            if num_grupos is None or num_grupos == '':
                cleaned_data['num_grupos'] = 0
            if num_classificados is None or num_classificados == '':
                cleaned_data['num_classificados'] = 0
        else:
            # Para outros formatos, os campos são obrigatórios
            if tipo_formato == 'misto':
                if not num_grupos or num_grupos <= 0:
                    self.add_error('num_grupos', 'Este campo é obrigatório para o formato Misto.')
                if not num_classificados or num_classificados <= 0:
                    self.add_error('num_classificados', 'Este campo é obrigatório para o formato Misto.')
        
        return cleaned_data


class TimeCampeonatoForm(forms.ModelForm):
    class Meta:
        model = TimeCampeonato
        fields = ['time', 'localizacao', 'campo_estadio', 'presidente']
        widgets = {
            'time': forms.Select(attrs={'class': 'form-input'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-input'}),
            'campo_estadio': forms.TextInput(attrs={'class': 'form-input'}),
            'presidente': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, tenant=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['time'].queryset = Time.objects.filter(tenant=tenant)


class ProfissionalForm(forms.ModelForm):
    class Meta:
        model = Profissional
        fields = ['nome', 'cpf', 'cidade', 'federacao', 'liga', 'telefone', 'chave_pix', 'tipo_chave_pix']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Digite o nome completo',
                'required': True
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'XXX.XXX.XXX-XX'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Digite a cidade',
                'required': True
            }),
            'federacao': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: FPF, CBF, etc.',
                'required': True
            }),
            'liga': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Digite a liga',
                'required': True
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '(11) 99999-9999'
            }),
            'chave_pix': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Digite a chave PIX'
            }),
            'tipo_chave_pix': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir campos obrigatórios explicitamente
        self.fields['nome'].required = True
        self.fields['cidade'].required = True
        self.fields['federacao'].required = True
        self.fields['liga'].required = True
        
        # Campos opcionais
        self.fields['cpf'].required = False
        self.fields['telefone'].required = False
        self.fields['chave_pix'].required = False
        self.fields['tipo_chave_pix'].required = False

    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        if not nome or not nome.strip():
            raise forms.ValidationError('O nome é obrigatório.')
        return nome.strip()

    def clean_cidade(self):
        cidade = self.cleaned_data.get('cidade')
        if not cidade or not cidade.strip():
            raise forms.ValidationError('A cidade é obrigatória.')
        return cidade.strip()

    def clean_federacao(self):
        federacao = self.cleaned_data.get('federacao')
        if not federacao or not federacao.strip():
            raise forms.ValidationError('A federação é obrigatória.')
        return federacao.strip()

    def clean_liga(self):
        liga = self.cleaned_data.get('liga')
        if not liga or not liga.strip():
            raise forms.ValidationError('A liga é obrigatória.')
        return liga.strip()

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove caracteres não numéricos
            cpf = ''.join(filter(str.isdigit, cpf))
            if cpf and len(cpf) != 11:
                raise forms.ValidationError('CPF deve ter 11 dígitos.')
        return cpf


class VincularJogadorForm(forms.ModelForm):
    class Meta:
        model = JogadorTimeCampeonato
        fields = ['jogador']
        widgets = {
            'jogador': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, tenant=None, time_campeonato=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            # Excluir jogadores já vinculados a este time neste campeonato
            jogadores_vinculados = JogadorTimeCampeonato.objects.filter(
                time_campeonato=time_campeonato,
                ativo=True
            ).values_list('jogador', flat=True)
            
            self.fields['jogador'].queryset = Jogador.objects.filter(
                tenant=tenant
            ).exclude(id__in=jogadores_vinculados)


class TimeCampeonatoEditForm(forms.ModelForm):
    class Meta:
        model = TimeCampeonato
        fields = ['localizacao', 'campo_estadio', 'presidente']
        widgets = {
            'localizacao': forms.TextInput(attrs={'class': 'form-input'}),
            'campo_estadio': forms.TextInput(attrs={'class': 'form-input'}),
            'presidente': forms.TextInput(attrs={'class': 'form-input'}),
        }

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'subtitulo', 'descricao']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'required': True}),
            'subtitulo': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'required': True}),
        }

class ImagemNoticiaForm(forms.ModelForm):
    class Meta:
        model = ImagemNoticia
        fields = ['imagem']
        widgets = {
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }

class MidiaImagemForm(forms.ModelForm):
    class Meta:
        model = MidiaImagem
        fields = ['imagem']
        widgets = {
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }

class PatrocinioForm(forms.ModelForm):
    class Meta:
        model = Patrocinio
        fields = ['imagem', 'nome']
        widgets = {
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
        }
