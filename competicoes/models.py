from django.db import models
from django.core.exceptions import ValidationError

class Campeonato(models.Model):
    TIPO_CHOICES = [
        ('e', 'Estadual'),
        ('r', 'Regional'),
        ('n', 'Nacional'),
        ('c', 'Continental'),
        ('m', 'Mundial'),
    ]

    nome = models.CharField(max_length=30)
    logo = models.ImageField(upload_to='logos/campeonatos/')
    temporada = models.IntegerField()
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    data_inicio = models.DateField()
    quantidade_equipes = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.nome} {self.temporada}'
    
class Clube(models.Model):
    nome = models.CharField(max_length=50)
    sigla = models.CharField(max_length=3)
    logo = models.ImageField(upload_to='logos/clubes/')
    tecnico = models.CharField(max_length=50, default='Interino')
    fundacao = models.DateField()
    estadio = models.CharField(max_length=50, null=True, blank=True)
    campeonatos = models.ManyToManyField(Campeonato, through='Participacao', related_name='clubes')

    def __str__(self):
        return f'{self.nome} ({self.sigla})'

class Participacao(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='participacoes')
    clube = models.ForeignKey(Clube, on_delete=models.CASCADE, related_name='participacoes')

    vitorias = models.PositiveIntegerField(default=0)
    empates = models.PositiveIntegerField(default=0)
    derrotas = models.PositiveIntegerField(default=0)
    gols_feitos = models.PositiveIntegerField(default=0)
    gols_sofridos = models.PositiveIntegerField(default=0)
    cartoes_amarelos = models.PositiveIntegerField(default=0)
    cartoes_vermelhos = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('campeonato', 'clube')
    
    def __str__(self):
        return f'{self.clube.sigla} no {self.campeonato.nome}'

class Escalacao(models.Model):
    clube = models.ForeignKey(Clube, on_delete=models.CASCADE)
    partida = models.ForeignKey('Partida', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.clube.nome} (partida {self.partida.__str__()})'

class EscalacaoSpace(models.Model):
    class PosicaoAssumidaEscalacaoSpace(models.TextChoices):
        GK = "GK", "Goleiro"
        CB = "CB", "Zagueiro Central"
        LB = "LB", "Lateral Esquerdo"
        RB = "RB", "Lateral Direito"
        LWB = "LWB", "Lateral Ofensivo Esquerdo"
        RWB = "RWB", "Lateral Ofensivo Direito"
        DM = "DM", "Volante"
        CM = "CM", "Meio Campo Central"
        AM = "AM", "Meia Ofensivo"
        LM = "LM", "Ala Esquerdo"
        RM = "RM", "Ala Direito"
        LW = "LW", "Ponta Esquerda"
        RW = "RW", "Ponta Direita"
        CF = "CF", "Centroavante"
        ST = "ST", "Atacante"

    escalacao = models.ForeignKey(Escalacao, on_delete=models.CASCADE)
    atleta = models.ForeignKey('Atleta', on_delete=models.CASCADE)

    numero_camisa = models.PositiveIntegerField()
    posicao_assumida = models.CharField(max_length=20, choices=PosicaoAssumidaEscalacaoSpace.choices)

class Gol(models.Model):
    clube = models.ForeignKey(Clube, on_delete=models.CASCADE, related_name='gols')
    partida = models.ForeignKey('Partida', on_delete=models.CASCADE, related_name='gols')

    atleta = models.ForeignKey('Atleta', on_delete=models.CASCADE, related_name='gols')
    minuto = models.PositiveIntegerField()

class Estatistica(models.Model):
    gols = models.IntegerField(null=True,blank=True)
    chutes = models.IntegerField(null=True,blank=True)
    chutes_a_gol = models.IntegerField(null=True,blank=True)
    porcentagem_posse_de_bola = models.IntegerField(null=True,blank=True) 
    passes = models.IntegerField(null=True,blank=True)
    porcentagem_precisao_de_passe = models.IntegerField(null=True,blank=True)
    faltas = models.IntegerField(null=True,blank=True)
    cartoes_amarelos = models.IntegerField(null=True,blank=True)
    cartoes_vermelhos = models.IntegerField(null=True,blank=True)
    escanteios = models.IntegerField(null=True,blank=True)
    impedimentos = models.IntegerField(null=True,blank=True)

class Partida(models.Model):
    class StatusPartida(models.TextChoices):
        PENDENTE = ('P', 'Pendente')
        FINALIZADA = ('F', 'Finalizada')
        ADIADA = ('A', 'Adiada')
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='partidas')
    rodada = models.IntegerField()
    status = models.CharField(max_length=20,choices=StatusPartida.choices, default=StatusPartida.PENDENTE)

    mandante = models.ForeignKey(Participacao, on_delete=models.CASCADE, related_name='partidas_mandante')
    visitante = models.ForeignKey(Participacao, on_delete=models.CASCADE, related_name='partidas_visitante')

    estatisticas_mandante = models.OneToOneField(Estatistica, on_delete=models.SET_NULL, null=True, blank=True, related_name='partida_como_estatisticas_mandante')
    estatisticas_visitante = models.OneToOneField(Estatistica, on_delete=models.SET_NULL, null=True, blank=True, related_name='partida_como_estatisticas_visitante')

    escalacao_mandante = models.OneToOneField(Escalacao, on_delete=models.SET_NULL, null=True, blank=True, related_name='partida_como_escalacao_mandante')
    escalacao_visitante = models.OneToOneField(Escalacao, on_delete=models.SET_NULL, null=True, blank=True, related_name='partida_como_escalacao_visitante')

    def __str__(self):
        return f'{self.mandante.clube.nome} x {self.visitante.clube.nome}'
    
    def clean(self): # método que define regras customizadas de validação. Ele é acionado durante o full_clean, que é o método que valida todo o objeto(inclusive, o clean é chamado no mesmo bloco que o clean_fields, que é quem valida se as regras grossas, como max_length ou IntegerField receber um número mesmo, estão sendo seguidas). O clean_fields é executado primeiro em relação ao clean
        super().clean() # o clean do Model é vazio, mas deixo essa linha aqui pra caso eu decida herdar de alguma classe diferente, pois ela pode ter alguma coisa no clean

        if self.mandante == self.visitante:
            raise ValidationError({'visitante': 'o mandante não pode jogar contra ele mesmo.'})
        if self.mandante.campeonato != self.campeonato:
            raise ValidationError({'mandante': f'O mandante não pertence ao campeonato {self.campeonato}'})
        if self.visitante.campeonato != self.campeonato:
            raise ValidationError({'visitante': f'O visitante não pertence ao campeonato {self.campeonato}'})
        
class Atleta(models.Model):
    class PosicaoPrincipalAtleta(models.TextChoices):
        GK = "GK", "Goleiro"
        CB = "CB", "Zagueiro Central"
        LB = "LB", "Lateral Esquerdo"
        RB = "RB", "Lateral Direito"
        LWB = "LWB", "Lateral Ofensivo Esquerdo"
        RWB = "RWB", "Lateral Ofensivo Direito"
        DM = "DM", "Volante"
        CM = "CM", "Meio Campo Central"
        AM = "AM", "Meia Ofensivo"
        LM = "LM", "Ala Esquerdo"
        RM = "RM", "Ala Direito"
        LW = "LW", "Ponta Esquerda"
        RW = "RW", "Ponta Direita"
        CF = "CF", "Centroavante"
        ST = "ST", "Atacante"

    nome = models.CharField(max_length=50)
    data_nascimento = models.DateField()
    altura = models.DecimalField(max_digits=3, decimal_places=2)
    peso = models.DecimalField(max_digits=3, decimal_places=1)
    nacionalidade = models.CharField(max_length=40)

    clube = models.ForeignKey(Clube, on_delete=models.SET_NULL, null=True, blank=True, related_name='elenco')
    posicao_principal = models.CharField(max_length=20, choices=PosicaoPrincipalAtleta.choices)

    def __str__(self):
        return f'{self.nome} | {self.clube}'
