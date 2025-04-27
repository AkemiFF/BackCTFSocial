import json

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.text import slugify
from rest_framework import serializers

from .models import ContentItem  # Assurez-vous d'importer les modèles
from .models import (Course, CourseTag, FileContent, ImageContent, LinkContent,
                     Module, Tag, TextContent, VideoContent)


class CourseCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'level', 'category', 'duration',
            'prerequisites', 'instructor', 'image', 'tags'
        ]

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        title = validated_data.get('title')

        # Générer un slug unique basé sur le title
        slug = slugify(title)
        unique_slug = slug
        counter = 1
        while Course.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{counter}"
            counter += 1

        validated_data['slug'] = unique_slug
        course_tags = []

        # Créer le cours avec le slug unique
        course = Course.objects.create(**validated_data)
        if tags_data and isinstance(tags_data[0], str):
            try:
                tags_data = json.loads(tags_data[0])  # Convertir la chaîne JSON en liste Python
            except json.JSONDecodeError:
                pass  # Si ce n'est pas du JSON valide, on le laisse tel quel

        # Traiter les tags correctement
        for tag_name in tags_data:
            tag_name = tag_name.strip()
            print(tag_name)  # Vérification de la sortie
            tag_slug = slugify(tag_name)
            tag_obj, _ = Tag.objects.get_or_create(name=tag_name, slug=tag_slug)
            course_tags.append(CourseTag(course=course, tag=tag_obj))


        # Optimisation : création en batch des CourseTag
        CourseTag.objects.bulk_create(course_tags)

        return course


class TextContentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextContent
        fields = ['content']

class ImageContentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageContent
        fields = ['image', 'position']

class VideoContentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContent
        fields = ['url', 'platform', 'video_file']

class FileContentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileContent
        fields = ['file', 'description']
        
    def create(self, validated_data):
        file = validated_data.get('file')
        if file and isinstance(file, InMemoryUploadedFile):
            validated_data['filename'] = file.name
            validated_data['file_size'] = file.size // 1024  # Convertir en KB
        return super().create(validated_data)

class LinkContentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkContent
        fields = ['url', 'description']

class ContentItemCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(required=False, write_only=True)  # Pour le texte
    image = serializers.ImageField(required=False, write_only=True)  # Pour l'image
    image_position = serializers.ChoiceField(
        choices=['left', 'center', 'right'],
        default='center',
        required=False,
        write_only=True
    )
    video_url = serializers.URLField(required=False, write_only=True)  # Pour la vidéo externe
    video_file = serializers.FileField(required=False, write_only=True)  # Pour la vidéo uploadée
    video_platform = serializers.ChoiceField(
        choices=['youtube', 'vimeo', 'local', 'upload'],
        default='youtube',
        required=False,
        write_only=True
    )
    file = serializers.FileField(required=False, write_only=True)  # Pour le fichier
    file_description = serializers.CharField(required=False, write_only=True)
    link_url = serializers.URLField(required=False, write_only=True)  # Pour le lien
    link_description = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = ContentItem
        fields = [
            'type', 'order', 'module',
            'content',  # Pour le texte
            'image', 'image_position',  # Pour l'image
            'video_url', 'video_file', 'video_platform',  # Pour la vidéo
            'file', 'file_description',  # Pour le fichier
            'link_url', 'link_description',  # Pour le lien
        ]
    
    def create(self, validated_data):
        content_type = validated_data.get('type')
        module = validated_data.get('module')
        order = validated_data.get('order', 0)
        
        # Créer l'élément de contenu de base
        content_item = ContentItem.objects.create(
            module=module,
            type=content_type,
            order=order
        )
        
        # Créer le contenu spécifique en fonction du type
        if content_type == 'text':
            content = validated_data.get('content', '')
            TextContent.objects.create(content_item=content_item, content=content)
        
        elif content_type == 'image':
            image = validated_data.get('image')
            position = validated_data.get('image_position', 'center')
            if image:
                ImageContent.objects.create(content_item=content_item, image=image, position=position)
        
        elif content_type == 'video':
            platform = validated_data.get('video_platform', 'youtube')
            url = validated_data.get('video_url', '')
            video_file = validated_data.get('video_file')
            
            if platform == 'upload' and video_file:
                VideoContent.objects.create(
                    content_item=content_item,
                    platform=platform,
                    video_file=video_file
                )
            elif platform in ['youtube', 'vimeo', 'local'] and url:
                VideoContent.objects.create(
                    content_item=content_item,
                    platform=platform,
                    url=url
                )
        
        elif content_type == 'file':
            file = validated_data.get('file')
            description = validated_data.get('file_description', '')
            
            if file:
                file_size = file.size // 1024  # Convertir en KB
                FileContent.objects.create(
                    content_item=content_item,
                    file=file,
                    filename=file.name,
                    description=description,
                    file_size=file_size
                )
        
        elif content_type == 'link':
            url = validated_data.get('link_url', '')
            description = validated_data.get('link_description', '')
            
            LinkContent.objects.create(
                content_item=content_item,
                url=url,
                description=description
            )
        
        return content_item

class ModuleCreateSerializer(serializers.ModelSerializer):
    content_items = ContentItemCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Module
        fields = ['course', 'title', 'duration', 'order', 'points', 'content_items']
    
    def create(self, validated_data):
        content_items_data = validated_data.pop('content_items', [])
        
        # Créer le module
        module = Module.objects.create(**validated_data)
        
        # Créer les éléments de contenu
        for item_data in content_items_data:
            item_data['module'] = module
            serializer = ContentItemCreateSerializer(data=item_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        
        return module
    
    
# serializers.py
from rest_framework import serializers

from .models import Module, QuizOption, QuizQuestion


class QuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id', 'text', 'is_correct']

class AdminQuizQuestionSerializer(serializers.ModelSerializer):
    # On peut envoyer une liste d'options lors de la création
    options = QuizOptionSerializer(many=True, required=False)
    module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())

    class Meta:
        model = QuizQuestion
        fields = ['id', 'module', 'question', 'type', 'order', 'options']

    def create(self, validated_data):
        # Récupération des options si présentes
        options_data = validated_data.pop('options', None)
        # Création de la question
        question = QuizQuestion.objects.create(**validated_data)
        # Si c'est une question à choix multiple et que des options ont été envoyées, les créer
        if options_data and validated_data.get('type') == 'multiple-choice':
            for option_data in options_data:
                QuizOption.objects.create(question=question, **option_data)
        return question
    
    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)

        # Mise à jour des champs de la question
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Mise à jour des options pour les questions à choix multiple
        if options_data is not None and instance.type == "multiple-choice":
            instance.options.all().delete()  # Supprime les anciennes options
            for option_data in options_data:
                QuizOption.objects.create(question=instance, **option_data)

        return instance