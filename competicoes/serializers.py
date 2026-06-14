from rest_framework import serializers
from .models import Campeonato, Clube, Participacao


class CampeonatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campeonato
        fields = '__all__'

class ClubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clube
        fields = '__all__'

class ParticipacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participacao
        fields = '__all__'