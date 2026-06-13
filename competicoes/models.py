from django.db import models


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
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE)
    clube = models.ForeignKey(Clube, on_delete=models.CASCADE)

    pontos = models.PositiveIntegerField(default=0)
    vitorias = models.PositiveIntegerField(default=0)
    empates = models.PositiveIntegerField(default=0)
    derrotas = models.PositiveIntegerField(default=0)
    gols_feitos = models.PositiveIntegerField(default=0)
    gols_sofridos = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('campeonato', 'clube')
    
    def __str__(self):
        return f'{self.clube.sigla} no {self.campeonato.nome}'
    