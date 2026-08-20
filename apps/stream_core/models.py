from django.db import models
#Classe que atua como modelo para o banco de dados
class ContentSource(models.Model):
    PLATAFORMAS = [
        ("TWITTER", "Twitter / X"), ("YOUTUBE", "Youtube"), ("INSTAGRAM", "Instagram"), ("NEWS", "Portal de Noticias"), ("REDDIT", "Reddit"), 
    ]
    
    name = models.CharField(max_length=100)
    plataform = models.CharField(max_length=20, choices=PLATAFORMAS)
    external_id = models.CharField(max_length=255, unique=True)
    feed_url = models.URLField(max_length=500, null=True, blank=True) #url do feed RSS, nem toda fonte tem
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True) #define automaticamente o valor de um campo de data ou hora para o momento exato em que um novo objeto é criado pela primeira vez
    
    
    def __str__(self):
        return f"{self.name} ({self.get_plataform_display()})"
    

class RawPost(models.Model):
    source = models.ForeignKey(
        ContentSource,
        on_delete=models.CASCADE, #Se a fonte for deletada, os posts dela vao junto
        related_name="posts"
    )
    external_id = models.CharField(max_length=255, unique=True)
    author = models.CharField( max_length=100, blank=True, null= True)
    text_content = models.TextField()
    engagement_score = models.IntegerField(default=0)
    published_at = models.DateTimeField()
    collected_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False) #indica se o post ja passou pela inteligencia NLP
    
    class Meta:
        indexes = [
            models.Index(fields=["is_processed", "published_at"]),
    ]
    def __str__(self):
        return f"post {self.external_id} - {self.source.name}"
    
class SentimentAnalysis(models.Model):
    SENTIMENTOS = [
        ("POS", "Positivo"), ("NEU", "Neutro"), ("NEG", "Negativo")
    ]
    post = models.OneToOneField(
        RawPost,
        on_delete=models.CASCADE,
        related_name="sentiment"
    )
    polarity_score = models.FloatField()
    label = models.CharField(max_length=3, choices=SENTIMENTOS)
    extracted_keywords = models.JSONField(default=list)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.post.external_id}: {self.get_label_display()} ({self.polarity_score}) "