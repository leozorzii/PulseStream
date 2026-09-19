from rest_framework import serializers
from apps.stream_core.models import ContentSource, RawPost, SentimentAnalysis

class ContentSourceSerializer(serializers.ModelSerializer):
    """Serializa objetos ContentSource para JSON e vice-versa.

    EXIGE O QUERYSET ANOTADO DO get_sources()
    post_count, pending_count e sentiment nao existem no model: sao anotacoes
    penduradas pelo selector. Serializar uma instancia crua de ContentSource
    aqui levanta AttributeError — e isso e proposital. A alternativa seria um
    getattr com 0 de reserva, que devolveria "0 posts" para uma fonte com
    trezentos e ninguem descobriria; melhor estourar na hora.
    """

    #declarados a mao porque sao anotacoes, e o ModelSerializer so enxerga campos
    #do model. read_only porque nao existe caminho de escrita para eles
    post_count = serializers.IntegerField(read_only=True)
    pending_count = serializers.IntegerField(read_only=True)
    sentiment = serializers.SerializerMethodField()

    class Meta:
        #qual model serializer traduzir
        model = ContentSource
        #campos que vao pro JSON na web
        fields = [
            "id", "name", "plataform", "external_id", "feed_url", "is_active",
            "created_at", "last_collected_at",
            "post_count", "pending_count", "sentiment",
        ]

    def get_sentiment(self, fonte):
        """Percentuais por label desta fonte, ou None se nada foi analisado.

        COMO FUNCIONA
        Soma as tres contagens anotadas pelo selector e converte cada uma em
        percentual sobre esse total. O total sai das analises, e nao de
        post_count: post pendente ainda nao tem sentimento, e dividir por ele
        diluiria os percentuais de uma fonte com fila grande — uma fonte 100%
        positiva com 90 pendentes apareceria como 10% positiva.

        POR QUE None, E NAO {POS: 0, NEU: 0, NEG: 0}
        Zerado leria como resultado calculado quando nada foi calculado. E a
        mesma decisao que /api/analytics/summary/ ja tomou na issue #31, entao
        as duas rotas concordam sobre o que "ainda nao ha o que resumir"
        parece. Um cliente que trate os dois casos igual vai desenhar um
        grafico de tres fatias zeradas e afirmar que a opiniao esta dividida.

        Args:
            fonte (ContentSource): a instancia anotada pelo get_sources()

        Returns:
            dict | None: {"POS", "NEU", "NEG"} em percentual, ou None quando a
                fonte ainda nao tem nenhuma analise
        """
        total = fonte.pos_count + fonte.neu_count + fonte.neg_count
        if total == 0:
            return None

        #as tres chaves sempre presentes, mesmo zeradas: um grafico desenhado
        #direto da resposta perderia series se a chave sumisse
        return {
            "POS": (fonte.pos_count / total) * 100,
            "NEU": (fonte.neu_count / total) * 100,
            "NEG": (fonte.neg_count / total) * 100,
        }


class RawPostSerializer(serializers.ModelSerializer):
    """Serializa objetos RawPost para JSON e vice-versa"""
    class Meta:
        model = RawPost
        fields = ["id", "source", "external_id", "text_content", "published_at", "is_processed"]


class FonteResumidaSerializer(serializers.ModelSerializer):
    """So o que um item do feed precisa saber da fonte dele."""

    class Meta:
        model = ContentSource
        fields = ["id", "name", "plataform"]


class AnaliseSerializer(serializers.ModelSerializer):
    """O sentimento de um post: label, intensidade e keywords.

    polarity_score e a razao de existir deste serializer para a #25: o label
    sozinho junta "morno" e "polarizado" no mesmo balde, e a intensidade e o
    que separa os dois.
    """

    class Meta:
        model = SentimentAnalysis
        fields = ["label", "polarity_score", "extracted_keywords"]


class PostAnalisadoSerializer(serializers.ModelSerializer):
    """Um post junto do sentimento que recebeu — o item do feed de evidencias.

    POR QUE A FONTE VAI ANINHADA
    RawPostSerializer devolve "source": 1, e o cliente teria que cruzar o id
    com /api/sources/. Aquela rota lista so as fontes ATIVAS por padrao, entao
    o post de uma fonte pausada resolveria para nada. Aninhado, o item se
    explica sozinho.

    EXIGE O QUERYSET DO get_analyzed_posts()
    source e sentiment sao lidos da instancia; sem o select_related do selector
    cada post custaria duas consultas a mais. E sentiment nao e opcional aqui:
    o selector so devolve post que tem analise.
    """

    source = FonteResumidaSerializer(read_only=True)
    sentiment = AnaliseSerializer(read_only=True)

    class Meta:
        model = RawPost
        fields = [
            "id", "external_id", "text_content", "author", "engagement_score",
            "published_at", "source", "sentiment",
        ]
